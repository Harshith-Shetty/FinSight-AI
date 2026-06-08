"""
Email service for FinSight AI.
Handles OTP generation, hashing, verification, and sending emails via Postmark SMTP.
"""

import secrets
import hashlib
import smtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import settings
from app.models.database import User, OTPToken, OTPPurpose
from app.services.email_templates import (
    verification_otp_email,
    password_reset_otp_email,
    welcome_email,
    upgrade_request_admin_email,
    upgrade_approved_email,
)


# ─── OTP Generation & Hashing ──────────────────────────────────────────────────

def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_otp(otp: str) -> str:
    """Hash an OTP using SHA-256 (fast, since OTPs are short-lived & rate-limited)."""
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    """Verify an OTP against its hash."""
    return hashlib.sha256(otp.encode("utf-8")).hexdigest() == otp_hash


# ─── OTP Database Operations ───────────────────────────────────────────────────

async def create_otp_token(
    db: AsyncSession,
    user: User,
    purpose: OTPPurpose,
) -> str:
    """
    Create a new OTP token for a user.
    Invalidates any existing unused OTPs for the same purpose.
    
    Returns:
        The plaintext OTP code (to be sent via email).
    """
    # Invalidate existing unused OTPs for this user + purpose
    result = await db.execute(
        select(OTPToken).where(
            and_(
                OTPToken.user_id == user.id,
                OTPToken.purpose == purpose,
                OTPToken.is_used == False,
            )
        )
    )
    existing_otps = result.scalars().all()
    for existing in existing_otps:
        existing.is_used = True
    
    # Generate new OTP
    otp_code = generate_otp()
    otp_token = OTPToken(
        user_id=user.id,
        otp_hash=hash_otp(otp_code),
        purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
    )
    
    db.add(otp_token)
    await db.flush()
    
    return otp_code


async def verify_otp_token(
    db: AsyncSession,
    user: User,
    otp_code: str,
    purpose: OTPPurpose,
) -> bool:
    """
    Verify an OTP code for a user.
    Marks the OTP as used if valid.
    
    Returns:
        True if valid, False otherwise.
    """
    result = await db.execute(
        select(OTPToken).where(
            and_(
                OTPToken.user_id == user.id,
                OTPToken.purpose == purpose,
                OTPToken.is_used == False,
                OTPToken.expires_at > datetime.utcnow(),
            )
        ).order_by(OTPToken.created_at.desc())
    )
    otp_token = result.scalar_one_or_none()
    
    if not otp_token:
        return False
    
    if not verify_otp_hash(otp_code, otp_token.otp_hash):
        return False
    
    # Mark as used
    otp_token.is_used = True
    await db.flush()
    
    return True


async def check_otp_cooldown(
    db: AsyncSession,
    user: User,
    purpose: OTPPurpose,
) -> Optional[int]:
    """
    Check if the user is within the OTP resend cooldown period.
    
    Returns:
        Seconds remaining in cooldown, or None if no cooldown active.
    """
    result = await db.execute(
        select(OTPToken).where(
            and_(
                OTPToken.user_id == user.id,
                OTPToken.purpose == purpose,
            )
        ).order_by(OTPToken.created_at.desc())
    )
    latest_otp = result.scalar_one_or_none()
    
    if not latest_otp:
        return None
    
    cooldown_end = latest_otp.created_at + timedelta(
        seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
    )
    now = datetime.utcnow()
    
    if now < cooldown_end:
        return int((cooldown_end - now).total_seconds())
    
    return None


# ─── Postmark SMTP Email Sending ────────────────────────────────────────────────

def _send_email_smtp_sync(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> bool:
    """
    Send an email via Postmark SMTP (synchronous, run in thread pool).
    
    Returns:
        True if sent successfully, False otherwise.
    """
    token = settings.POSTMARK_SERVER_TOKEN
    
    if not token or token == "your-postmark-server-token":
        print(f"[EMAIL] Postmark not configured. Would have sent to: {to_email}")
        print(f"[EMAIL] Subject: {subject}")
        return True
    
    # Build MIME message
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.POSTMARK_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["X-PM-Message-Stream"] = settings.POSTMARK_MESSAGE_STREAM
    
    # Attach plaintext and HTML (HTML last = preferred)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    
    try:
        with smtplib.SMTP(settings.POSTMARK_SMTP_HOST, settings.POSTMARK_SMTP_PORT) as server:
            server.starttls()
            server.login(token, token)  # Postmark uses token as both username & password
            server.send_message(msg)
        
        print(f"[EMAIL] Sent '{subject}' to {to_email}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Error sending to {to_email}: {e}")
        return False


async def _send_email_via_postmark(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> bool:
    """
    Async wrapper around SMTP sending — runs the blocking SMTP call in a thread pool.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _send_email_smtp_sync, to_email, subject, html_body, text_body
    )


# ─── High-Level Email Functions ─────────────────────────────────────────────────

async def send_verification_email(user_email: str, otp_code: str) -> bool:
    """Send email verification OTP."""
    html, text = verification_otp_email(otp_code, user_email)
    return await _send_email_via_postmark(
        to_email=user_email,
        subject="Verify your email — FinSight AI",
        html_body=html,
        text_body=text,
    )


async def send_password_reset_email(user_email: str, otp_code: str) -> bool:
    """Send password reset OTP."""
    html, text = password_reset_otp_email(otp_code, user_email)
    return await _send_email_via_postmark(
        to_email=user_email,
        subject="Reset your password — FinSight AI",
        html_body=html,
        text_body=text,
    )


async def send_welcome_email(user_email: str) -> bool:
    """Send welcome email after successful verification."""
    html, text = welcome_email(user_email)
    return await _send_email_via_postmark(
        to_email=user_email,
        subject="Welcome to FinSight AI! 🎉",
        html_body=html,
        text_body=text,
    )


async def send_plan_upgrade_request_email(user_email: str, reason: str, request_id: str) -> bool:
    """Send plan upgrade request to developer."""
    admin_email = "developer.finSightAI@harshithshetty.dev"
    html, text = upgrade_request_admin_email(user_email, reason, request_id)
    return await _send_email_via_postmark(
        to_email=admin_email,
        subject=f"New Plan Upgrade Request from {user_email}",
        html_body=html,
        text_body=text,
    )


async def send_plan_upgrade_approved_email(user_email: str, admin_email: str, plan: str) -> bool:
    """Send plan upgrade approval email to user, and notify developer."""
    # Notify developer
    dev_email = "developer.finSightAI@harshithshetty.dev"
    from app.services.email_templates import dev_upgrade_approved_email
    dev_html, dev_text = dev_upgrade_approved_email(user_email, admin_email, plan)
    
    await _send_email_via_postmark(
        to_email=dev_email,
        subject=f"Upgrade Approved: {user_email}",
        html_body=dev_html,
        text_body=dev_text,
    )
    
    # Send actual approval email to user
    html, text = upgrade_approved_email(user_email)
    return await _send_email_via_postmark(
        to_email=user_email,
        subject="Your FinSight AI Premium upgrade is approved!",
        html_body=html,
        text_body=text,
    )

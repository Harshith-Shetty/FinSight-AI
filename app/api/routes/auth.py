"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.schemas import (
    UserRegister, UserLogin, Token, UserResponse, TokenUsageResponse,
    RegisterResponse, VerifyEmailRequest, ResendOTPRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.models.database import User, OTPPurpose
from app.services.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from app.services.email_service import (
    create_otp_token, verify_otp_token, check_otp_cooldown,
    send_verification_email, send_password_reset_email, send_welcome_email,
)
from app.core.database import get_db
from app.core.permissions import get_token_quota_status
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    
    After registration, a 6-digit OTP will be sent to the email for verification.
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user (unverified)
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        is_verified=False,
    )
    
    db.add(new_user)
    await db.flush()
    
    # Generate and send verification OTP
    otp_code = await create_otp_token(db, new_user, OTPPurpose.EMAIL_VERIFICATION)
    await send_verification_email(new_user.email, otp_code)
    
    await db.commit()
    
    return RegisterResponse(
        email=new_user.email,
        email_verification_required=True,
        message="Account created. Please check your email for the verification code.",
    )


@router.post("/verify-email", response_model=Token)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email with 6-digit OTP code.
    
    On success, marks the user as verified, sends a welcome email,
    and returns a JWT token (auto-login).
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Verify OTP
    is_valid = await verify_otp_token(db, user, data.otp, OTPPurpose.EMAIL_VERIFICATION)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    # Mark as verified
    user.is_verified = True
    user.last_login = datetime.utcnow()
    
    await db.commit()
    
    # Send welcome email (fire and forget, don't fail if it doesn't send)
    try:
        await send_welcome_email(user.email)
    except Exception:
        pass
    
    # Create access token (auto-login)
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/resend-otp")
async def resend_otp(
    data: ResendOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend OTP code for email verification or password reset.
    Has a cooldown of 60 seconds between resends.
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal whether email exists for security
        return {"message": "If the email is registered, a new code has been sent."}
    
    # Determine purpose
    if data.purpose == "password_reset":
        purpose = OTPPurpose.PASSWORD_RESET
    else:
        purpose = OTPPurpose.EMAIL_VERIFICATION
        # Don't resend verification OTP if already verified
        if user.is_verified:
            return {"message": "Email is already verified."}
    
    # Check cooldown
    cooldown_remaining = await check_otp_cooldown(db, user, purpose)
    if cooldown_remaining is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {cooldown_remaining} seconds before requesting a new code."
        )
    
    # Generate and send new OTP
    otp_code = await create_otp_token(db, user, purpose)
    
    if purpose == OTPPurpose.PASSWORD_RESET:
        await send_password_reset_email(user.email, otp_code)
    else:
        await send_verification_email(user.email, otp_code)
    
    await db.commit()
    
    return {"message": "A new verification code has been sent to your email."}


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and receive JWT access token.
    
    - **email**: User email
    - **password**: User password
    
    Returns 403 if the email has not been verified yet.
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification code."
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset OTP.
    
    Sends a 6-digit OTP to the user's email if the account exists.
    For security, always returns success even if the email is not found.
    """
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal whether email exists
        return {"message": "If the email is registered, a password reset code has been sent."}
    
    # Check cooldown
    cooldown_remaining = await check_otp_cooldown(db, user, OTPPurpose.PASSWORD_RESET)
    if cooldown_remaining is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {cooldown_remaining} seconds before requesting a new code."
        )
    
    # Generate and send password reset OTP
    otp_code = await create_otp_token(db, user, OTPPurpose.PASSWORD_RESET)
    await send_password_reset_email(user.email, otp_code)
    
    await db.commit()
    
    return {"message": "If the email is registered, a password reset code has been sent."}


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using OTP code.
    
    Verifies the OTP and updates the user's password.
    """
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify OTP
    is_valid = await verify_otp_token(db, user, data.otp, OTPPurpose.PASSWORD_RESET)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )
    
    # Update password
    user.password_hash = get_password_hash(data.new_password)
    
    await db.commit()
    
    return {"message": "Password has been reset successfully. You can now log in with your new password."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user information from JWT token.
    """
    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user



@router.get("/me/tokens", response_model=TokenUsageResponse)
async def get_current_user_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's token usage and quota for the month.
    """
    quota = await get_token_quota_status(current_user, db)
    return quota


@router.post("/resend-welcome", status_code=status.HTTP_200_OK)
async def resend_welcome(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend the welcome email to a user (can be used from Swagger).
    """
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    await send_welcome_email(user.email)
    
    return {"message": "Welcome email sent successfully."}

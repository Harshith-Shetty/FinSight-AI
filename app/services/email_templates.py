"""
Premium HTML email templates for FinSight AI.
All templates use inline CSS for maximum email client compatibility.
"""


def _base_template(content: str, preview_text: str = "") -> str:
    """
    Wrap email content in a premium dark-themed base layout.
    Uses inline CSS for maximum email client compatibility.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>FinSight AI</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #0f0f23; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <!-- Preview text (hidden) -->
    <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">
        {preview_text}
    </div>
    
    <!-- Main container -->
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0f0f23;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <!-- Card container -->
                <table role="presentation" cellpadding="0" cellspacing="0" width="600" style="max-width: 600px; width: 100%;">
                    
                    <!-- Logo Header -->
                    <tr>
                        <td align="center" style="padding-bottom: 32px;">
                            <h1 style="margin: 0 0 6px; font-size: 26px; font-weight: 800; color: #f1f5f9; letter-spacing: -0.5px;">
                                FinSight <span style="background: linear-gradient(135deg, #818cf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; color: #818cf8;">AI</span>
                            </h1>
                            <p style="margin: 0; font-size: 13px; color: #64748b; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase;">
                                AI-Powered Financial Intelligence
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content Card -->
                    <tr>
                        <td style="background-color: #1a1a2e; border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2); overflow: hidden;">
                            <!-- Gradient accent bar -->
                            <div style="height: 4px; background: linear-gradient(90deg, #6366f1, #8b5cf6, #a78bfa);"></div>
                            
                            <!-- Content -->
                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="padding: 40px 40px 32px;">
                                        {content}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding-top: 32px; text-align: center;">
                            <p style="margin: 0 0 8px; color: #64748b; font-size: 12px; line-height: 1.5;">
                                This email was sent by FinSight AI
                            </p>
                            <p style="margin: 0 0 16px; color: #475569; font-size: 11px; line-height: 1.5;">
                                If you didn't request this email, you can safely ignore it.
                            </p>
                            <!-- Author Credentials -->
                            <div style="border-top: 1px solid rgba(99, 102, 241, 0.15); padding-top: 16px; margin-top: 8px;">
                                <p style="margin: 0 0 8px; color: #94a3b8; font-size: 11px; line-height: 1.5; font-weight: 500;">
                                    Developed by <strong style="color: #c7d2fe;">Harshith Shetty</strong>
                                </p>
                                <p style="margin: 0; font-size: 11px; line-height: 1.5;">
                                    <a href="https://harshithshetty.dev" target="_blank" style="color: #818cf8; text-decoration: none; margin: 0 8px; font-weight: 600;">Portfolio</a> |
                                    <a href="https://github.harshithshetty.dev" target="_blank" style="color: #818cf8; text-decoration: none; margin: 0 8px; font-weight: 600;">GitHub</a> |
                                    <a href="https://linkedin.harshithshetty.dev" target="_blank" style="color: #818cf8; text-decoration: none; margin: 0 8px; font-weight: 600;">LinkedIn</a>
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def verification_otp_email(otp_code: str, user_email: str) -> tuple[str, str]:
    """
    Generate verification OTP email.
    
    Returns:
        Tuple of (html_content, plaintext_content)
    """
    content = f"""
        <h2 style="margin: 0 0 8px; color: #f1f5f9; font-size: 22px; font-weight: 700;">
            Verify Your Email
        </h2>
        <p style="margin: 0 0 24px; color: #94a3b8; font-size: 15px; line-height: 1.6;">
            Welcome! Use the verification code below to complete your registration.
        </p>
        
        <!-- OTP Code Box -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
            <tr>
                <td align="center">
                    <div style="background-color: #16163a; border: 2px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 24px 32px; display: inline-block;">
                        <p style="margin: 0 0 8px; color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;">
                            Verification Code
                        </p>
                        <p style="margin: 0; color: #818cf8; font-size: 36px; font-weight: 800; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                            {otp_code}
                        </p>
                    </div>
                </td>
            </tr>
        </table>
        
        <!-- Info -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
            <tr>
                <td style="background-color: rgba(99, 102, 241, 0.08); border-radius: 8px; padding: 16px;">
                    <table role="presentation" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="padding-right: 12px; vertical-align: top;">
                                <span style="font-size: 18px;">&#x23F0;</span>
                            </td>
                            <td>
                                <p style="margin: 0; color: #94a3b8; font-size: 13px; line-height: 1.5;">
                                    This code will expire in <strong style="color: #c7d2fe;">10 minutes</strong>. 
                                    Don't share it with anyone.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <p style="margin: 0; color: #64748b; font-size: 13px;">
            If you didn't create an account with FinSight AI, please ignore this email.
        </p>
    """
    
    html = _base_template(content, f"Your FinSight AI verification code is {otp_code}")
    
    plaintext = f"""FinSight AI — Email Verification

Your verification code is: {otp_code}

This code will expire in 10 minutes. Don't share it with anyone.

If you didn't create an account with FinSight AI, please ignore this email.

---
Developed by Harshith Shetty
Portfolio: https://harshithshetty.dev | GitHub: https://github.harshithshetty.dev | LinkedIn: https://linkedin.harshithshetty.dev
"""
    
    return html, plaintext


def password_reset_otp_email(otp_code: str, user_email: str) -> tuple[str, str]:
    """
    Generate password reset OTP email.
    
    Returns:
        Tuple of (html_content, plaintext_content)
    """
    content = f"""
        <h2 style="margin: 0 0 8px; color: #f1f5f9; font-size: 22px; font-weight: 700;">
            Reset Your Password
        </h2>
        <p style="margin: 0 0 24px; color: #94a3b8; font-size: 15px; line-height: 1.6;">
            We received a request to reset the password for your account. Use the code below to set a new password.
        </p>
        
        <!-- OTP Code Box -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
            <tr>
                <td align="center">
                    <div style="background-color: #16163a; border: 2px solid rgba(251, 146, 60, 0.3); border-radius: 12px; padding: 24px 32px; display: inline-block;">
                        <p style="margin: 0 0 8px; color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;">
                            Reset Code
                        </p>
                        <p style="margin: 0; color: #fb923c; font-size: 36px; font-weight: 800; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                            {otp_code}
                        </p>
                    </div>
                </td>
            </tr>
        </table>
        
        <!-- Security Warning -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
            <tr>
                <td style="background-color: rgba(251, 146, 60, 0.08); border-radius: 8px; padding: 16px;">
                    <table role="presentation" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="padding-right: 12px; vertical-align: top;">
                                <span style="font-size: 18px;">&#x1F6E1;&#xFE0F;</span>
                            </td>
                            <td>
                                <p style="margin: 0; color: #94a3b8; font-size: 13px; line-height: 1.5;">
                                    This code will expire in <strong style="color: #fed7aa;">10 minutes</strong>. 
                                    For security, never share this code with anyone.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- Didn't request -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-top: 1px solid rgba(100, 116, 139, 0.2); padding-top: 16px;">
            <tr>
                <td style="padding-top: 16px;">
                    <p style="margin: 0; color: #64748b; font-size: 13px; line-height: 1.6;">
                        &#x26A0;&#xFE0F; <strong>Didn't request this?</strong> If you didn't request a password reset, 
                        your account is safe. Someone may have entered your email by mistake. No action is needed.
                    </p>
                </td>
            </tr>
        </table>
    """
    
    html = _base_template(content, f"Your FinSight AI password reset code is {otp_code}")
    
    plaintext = f"""FinSight AI — Password Reset

Your password reset code is: {otp_code}

This code will expire in 10 minutes. For security, never share this code with anyone.

If you didn't request a password reset, your account is safe. No action is needed.

---
Developed by Harshith Shetty
Portfolio: https://harshithshetty.dev | GitHub: https://github.harshithshetty.dev | LinkedIn: https://linkedin.harshithshetty.dev
"""
    
    return html, plaintext


def welcome_email(user_email: str, app_url: str = "http://localhost:3000") -> tuple[str, str]:
    """
    Generate welcome email sent after successful verification.
    
    Returns:
        Tuple of (html_content, plaintext_content)
    """
    content = f"""
        <h2 style="margin: 0 0 8px; color: #f1f5f9; font-size: 22px; font-weight: 700;">
            Welcome to FinSight AI! &#x1F389;
        </h2>
        <p style="margin: 0 0 28px; color: #94a3b8; font-size: 15px; line-height: 1.6;">
            Your email has been verified and your account is all set. You're ready to harness the power of AI-driven financial intelligence.
        </p>
        
        <!-- Feature Cards -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
            <!-- Feature 1 -->
            <tr>
                <td style="padding-bottom: 12px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <td style="background-color: #16163a; border-radius: 10px; padding: 16px;">
                                <table role="presentation" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding-right: 14px; vertical-align: top;">
                                            <div style="width: 36px; height: 36px; background-color: rgba(99, 102, 241, 0.15); border-radius: 8px; text-align: center; line-height: 36px; font-size: 18px;">
                                                &#x1F4AC;
                                            </div>
                                        </td>
                                        <td>
                                            <p style="margin: 0 0 2px; color: #e2e8f0; font-size: 14px; font-weight: 600;">AI Chat</p>
                                            <p style="margin: 0; color: #94a3b8; font-size: 13px; line-height: 1.4;">
                                                Ask questions about financial documents with AI-powered analysis
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <!-- Feature 2 -->
            <tr>
                <td style="padding-bottom: 12px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <td style="background-color: #16163a; border-radius: 10px; padding: 16px;">
                                <table role="presentation" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding-right: 14px; vertical-align: top;">
                                            <div style="width: 36px; height: 36px; background-color: rgba(139, 92, 246, 0.15); border-radius: 8px; text-align: center; line-height: 36px; font-size: 18px;">
                                                &#x1F4C4;
                                            </div>
                                        </td>
                                        <td>
                                            <p style="margin: 0 0 2px; color: #e2e8f0; font-size: 14px; font-weight: 600;">Document Analysis</p>
                                            <p style="margin: 0; color: #94a3b8; font-size: 13px; line-height: 1.4;">
                                                Upload PDFs and get instant insights from SEC filings and reports
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <!-- Feature 3 -->
            <tr>
                <td>
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <td style="background-color: #16163a; border-radius: 10px; padding: 16px;">
                                <table role="presentation" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding-right: 14px; vertical-align: top;">
                                            <div style="width: 36px; height: 36px; background-color: rgba(167, 139, 250, 0.15); border-radius: 8px; text-align: center; line-height: 36px; font-size: 18px;">
                                                &#x1F4CA;
                                            </div>
                                        </td>
                                        <td>
                                            <p style="margin: 0 0 2px; color: #e2e8f0; font-size: 14px; font-weight: 600;">Risk Analysis</p>
                                            <p style="margin: 0; color: #94a3b8; font-size: 13px; line-height: 1.4;">
                                                Automated sentiment scoring and risk factor identification
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- CTA Button -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
            <tr>
                <td align="center">
                    <a href="{app_url}/chat" style="display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 600; padding: 14px 32px; border-radius: 10px; letter-spacing: 0.3px;">
                        Start Exploring &rarr;
                    </a>
                </td>
            </tr>
        </table>
        
        <p style="margin: 0; color: #64748b; font-size: 13px; text-align: center;">
            Have questions? Just reply to this email and we'll help you out.
        </p>
    """
    
    html = _base_template(content, "Your FinSight AI account is ready! Start analyzing financial data with AI.")
    
    plaintext = f"""Welcome to FinSight AI!

Your email has been verified and your account is all set.

Here's what you can do:
- AI Chat: Ask questions about financial documents
- Document Analysis: Upload PDFs for instant insights
- Risk Analysis: Automated sentiment scoring

Get started: {app_url}/chat

Have questions? Just reply to this email.

---
Developed by Harshith Shetty
Portfolio: https://harshithshetty.dev | GitHub: https://github.harshithshetty.dev | LinkedIn: https://linkedin.harshithshetty.dev
"""
    
    return html, plaintext

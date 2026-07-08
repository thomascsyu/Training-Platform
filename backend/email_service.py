import httpx
from typing import Optional

from config import BREVO_API_KEY, EMAIL_FROM, EMAIL_FROM_NAME, FRONTEND_URL, logger


async def send_brevo_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
):
    if not BREVO_API_KEY:
        logger.warning("Brevo API key not configured, skipping email")
        return None

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": EMAIL_FROM_NAME, "email": EMAIL_FROM},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if text_content:
        payload["textContent"] = text_content

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201, 202]:
                logger.info("Email sent successfully to %s", to_email)
                return response.json()
            logger.error(
                "Failed to send email: %s - %s", response.status_code, response.text
            )
            return None
    except Exception as exc:
        logger.error("Email sending error: %s", exc)
        return None


async def send_enrollment_email(
    user_email: str, user_name: str, course_title: str, course_id: str
):
    subject = f"Welcome to {course_title}! - LearnHub"
    html_content = f"""
    <html>
    <body style="font-family: 'IBM Plex Sans', Arial, sans-serif; background-color: #F4F5F7; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #002FA7; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">You're Enrolled!</h1>
            </div>
            <div style="padding: 30px;">
                <p style="color: #0A0B10; font-size: 16px;">Hi {user_name},</p>
                <p style="color: #64748B; font-size: 14px; line-height: 1.6;">
                    Congratulations! You have been successfully enrolled in:
                </p>
                <div style="background-color: #F4F5F7; padding: 20px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #002FA7;">
                    <h2 style="color: #0A0B10; margin: 0 0 10px 0; font-size: 18px;">{course_title}</h2>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/courses/{course_id}"
                       style="background-color: #002FA7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: 500; display: inline-block;">
                        Start Learning
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_brevo_email(user_email, user_name, subject, html_content)


async def send_progress_email(
    user_email: str,
    user_name: str,
    course_title: str,
    progress: int,
    course_id: str,
):
    subject = f"Progress Update: {progress}% Complete - {course_title}"
    html_content = f"""
    <html>
    <body style="font-family: 'IBM Plex Sans', Arial, sans-serif; background-color: #F4F5F7; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 4px; overflow: hidden;">
            <div style="background-color: #002FA7; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Progress Update</h1>
            </div>
            <div style="padding: 30px;">
                <p style="color: #0A0B10; font-size: 16px;">Hi {user_name},</p>
                <p style="color: #64748B; font-size: 14px;">Great progress on <strong>{course_title}</strong>!</p>
                <div style="background-color: #E2E8F0; height: 24px; border-radius: 12px; overflow: hidden; margin: 20px 0;">
                    <div style="background-color: #002FA7; height: 100%; width: {progress}%;"></div>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/courses/{course_id}"
                       style="background-color: #002FA7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px;">
                        Continue Learning
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_brevo_email(user_email, user_name, subject, html_content)


async def send_certificate_email(
    user_email: str,
    user_name: str,
    course_title: str,
    certificate_id: str,
    score: int,
):
    subject = f"Congratulations! Certificate for {course_title}"
    html_content = f"""
    <html>
    <body style="font-family: 'IBM Plex Sans', Arial, sans-serif; background-color: #F4F5F7; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 4px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #002FA7 0%, #0A0B10 100%); padding: 40px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Congratulations!</h1>
            </div>
            <div style="padding: 30px;">
                <p style="color: #0A0B10;">Dear {user_name},</p>
                <p style="color: #64748B;">You completed <strong>{course_title}</strong> with a score of <strong>{score}%</strong>.</p>
                <p style="color: #94A3B8; font-size: 12px;">Certificate ID: {certificate_id}</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/certificates"
                       style="background-color: #002FA7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px;">
                        View Your Certificate
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_brevo_email(user_email, user_name, subject, html_content)


async def send_password_reset_email(
    user_email: str,
    user_name: str,
    reset_link: str,
    expires_in_minutes: int,
):
    subject = "Reset your LearnHub password"
    html_content = f"""
    <html>
    <body style="font-family: 'IBM Plex Sans', Arial, sans-serif; background-color: #F4F5F7; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 4px; overflow: hidden;">
            <div style="background-color: #002FA7; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Password Reset Request</h1>
            </div>
            <div style="padding: 30px;">
                <p style="color: #0A0B10; font-size: 16px;">Hi {user_name},</p>
                <p style="color: #64748B; font-size: 14px; line-height: 1.6;">
                    We received a request to reset your LearnHub password.
                    Click the button below to choose a new password.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}"
                       style="background-color: #002FA7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: 500; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #64748B; font-size: 13px; line-height: 1.6;">
                    This link expires in {expires_in_minutes} minutes.
                    If you did not request this, you can safely ignore this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    text_content = (
        f"Hi {user_name},\n\n"
        f"We received a request to reset your LearnHub password.\n"
        f"Use this link to set a new password: {reset_link}\n\n"
        f"This link expires in {expires_in_minutes} minutes.\n"
        "If you did not request this, you can ignore this email."
    )
    return await send_brevo_email(
        user_email,
        user_name,
        subject,
        html_content,
        text_content=text_content,
    )

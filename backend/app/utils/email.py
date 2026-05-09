"""
Email delivery utilities.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


async def send_email(to: str, subject: str, html_body: str) -> None:
    """
    Send an HTML email using SMTP settings.

    If SMTP credentials are incomplete, skip delivery so local development and
    tests do not fail because email is not configured.
    """
    if not settings.EMAIL_FROM or not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as server:
        if settings.EMAIL_USE_TLS:
            server.starttls()
        server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, to, msg.as_string())

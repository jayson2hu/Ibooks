"""
Email delivery utilities.
"""
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings
from app.utils.logging import get_logger


logger = get_logger(__name__)
SMTP_TIMEOUT_SECONDS = 10


def _smtp_is_configured() -> bool:
    """Return whether the credentials required by the SMTP client are set."""
    return bool(
        settings.EMAIL_FROM
        and settings.EMAIL_USERNAME
        and settings.EMAIL_PASSWORD
    )


def _send_email_sync(to: str, subject: str, html_body: str) -> None:
    """Perform the blocking SMTP exchange outside the application event loop."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(
        settings.EMAIL_SMTP_HOST,
        settings.EMAIL_SMTP_PORT,
        timeout=SMTP_TIMEOUT_SECONDS,
    ) as server:
        if settings.EMAIL_USE_TLS:
            server.starttls()
        server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, to, msg.as_string())


async def send_email(to: str, subject: str, html_body: str) -> bool:
    """
    Send an HTML email using SMTP settings.

    Email is a best-effort external side effect. Missing credentials and SMTP
    delivery errors are logged without message contents or recipient data and
    reported to the caller as ``False``.
    """
    if not _smtp_is_configured():
        logger.info(
            "Email delivery skipped because SMTP is not configured",
            extra={
                "event": "email_delivery_skipped",
                "reason": "smtp_not_configured",
            },
        )
        return False

    try:
        await asyncio.to_thread(_send_email_sync, to, subject, html_body)
    except (OSError, smtplib.SMTPException) as exc:
        logger.warning(
            "Email delivery failed",
            extra={
                "event": "email_delivery_failed",
                "error_type": type(exc).__name__,
            },
        )
        return False

    logger.info(
        "Email delivered",
        extra={"event": "email_delivery_succeeded"},
    )
    return True

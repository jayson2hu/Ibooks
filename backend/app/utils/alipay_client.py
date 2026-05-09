"""
Alipay SDK client wrapper.
"""
from app.config import settings

try:
    from alipay import AliPay
except ImportError:  # pragma: no cover - handled by runtime configuration
    AliPay = None


ALIPAY_GATEWAY = "https://openapi.alipay.com/gateway.do"
ALIPAY_SANDBOX_GATEWAY = "https://openapi.alipaydev.com/gateway.do"


def normalize_key(key: str) -> str:
    """Normalize escaped newlines from environment variables."""
    return key.replace("\\n", "\n")


def get_alipay_client():
    """Create an AliPay SDK client from settings."""
    if AliPay is None:
        raise RuntimeError("alipay-sdk-python is not installed")

    if not settings.ALIPAY_APP_ID or not settings.ALIPAY_PRIVATE_KEY or not settings.ALIPAY_PUBLIC_KEY:
        raise RuntimeError("Alipay configuration is incomplete")

    return AliPay(
        appid=settings.ALIPAY_APP_ID,
        app_notify_url=None,
        app_private_key_string=normalize_key(settings.ALIPAY_PRIVATE_KEY),
        alipay_public_key_string=normalize_key(settings.ALIPAY_PUBLIC_KEY),
        sign_type="RSA2",
        debug=settings.ALIPAY_SANDBOX,
    )


def get_alipay_gateway() -> str:
    """Return the correct Alipay gateway URL."""
    return ALIPAY_SANDBOX_GATEWAY if settings.ALIPAY_SANDBOX else ALIPAY_GATEWAY

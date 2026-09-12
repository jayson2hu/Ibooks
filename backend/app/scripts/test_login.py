import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.scripts.secure_inputs import read_secret  # noqa: E402


def main() -> None:
    """Test admin login without embedding credentials or printing the token."""
    base_url = os.environ.get("IBOOKS_API_BASE_URL", "http://127.0.0.1:8000")
    admin_email = os.environ.get("IBOOKS_ADMIN_EMAIL", "admin@example.com")
    admin_password = read_secret(
        "IBOOKS_ADMIN_PASSWORD",
        prompt="Admin password: ",
        confirmation_prompt=None,
    )

    url = f"{base_url.rstrip('/')}/api/v1/auth/login"
    try:
        response = httpx.post(
            url,
            json={"email": admin_email, "password": admin_password},
            timeout=10,
        )
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            token = response.json().get("access_token")
            if not token:
                raise RuntimeError("Login succeeded but no access token was returned")
            print("✓ Login successful; access token received but not displayed.")
        else:
            print("✗ Login failed; response body suppressed.")
    except httpx.RequestError as exc:
        print(f"Request failed: {type(exc).__name__}")
        raise


if __name__ == "__main__":
    main()

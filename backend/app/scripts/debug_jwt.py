import sys
from pathlib import Path

import jwt

# Add backend directory to python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import settings  # noqa: E402
from app.utils.security import create_access_token, decode_access_token  # noqa: E402


def main() -> None:
    """Create and verify a token without disclosing secrets or token material."""
    print(f"Algorithm: {settings.JWT_ALGORITHM}")
    print("Signing key: configured (value and fingerprint intentionally hidden)")

    data = {"sub": 1, "email": "admin@example.com", "role": "admin"}
    token = create_access_token(data)
    print("Generated token: created successfully (value intentionally hidden)")

    decoded = decode_access_token(token)
    print(f"Decoded internal claims: {decoded}")

    if decoded is None:
        print("FAILED to decode internal token!")
        try:
            jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except Exception as exc:
            print(f"Decode error type: {type(exc).__name__}")


if __name__ == "__main__":
    main()

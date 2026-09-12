import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import delete  # noqa: E402

from app.database import AsyncSessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.scripts.secure_inputs import (  # noqa: E402
    read_secret,
    require_confirmation,
)
from app.utils.security import get_password_hash  # noqa: E402


async def recreate_admin():
    admin_email = os.environ.get("IBOOKS_ADMIN_EMAIL", "admin@example.com")
    admin_username = os.environ.get("IBOOKS_ADMIN_USERNAME", "admin")
    require_confirmation(
        "IBOOKS_ADMIN_RECREATE_CONFIRM",
        expected="RECREATE_ADMIN",
        prompt=(
            f"This will replace {admin_email}. Type RECREATE_ADMIN to continue: "
        ),
    )
    admin_password = read_secret(
        "IBOOKS_ADMIN_PASSWORD",
        prompt="New admin password: ",
        confirmation_prompt="Confirm new admin password: ",
    )

    async with AsyncSessionLocal() as db:
        # Delete and recreate in one transaction so a failed insert rolls back.
        print("Deleting existing admin user...")
        result = await db.execute(
            delete(User).where(User.email == admin_email)
        )
        print(f"✓ Deleted {result.rowcount} user(s)")

        # Create new admin user with correct fields
        print("\nCreating new admin user...")
        admin = User(
            email=admin_email,
            username=admin_username,
            password_hash=get_password_hash(admin_password),
            role="admin",
            status="active",
            is_email_verified=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        print("✓ Created admin user:")
        print(f"  - Email: {admin.email}")
        print(f"  - Username: {admin.username}")
        print(f"  - Role: {admin.role}")
        print(f"  - Status: {admin.status}")
        print("  - Password was supplied securely and was not printed.")


if __name__ == "__main__":
    asyncio.run(recreate_admin())

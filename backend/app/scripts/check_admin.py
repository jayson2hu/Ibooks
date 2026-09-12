import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import func, select  # noqa: E402

from app.database import AsyncSessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.scripts.secure_inputs import read_secret  # noqa: E402
from app.utils.security import get_password_hash  # noqa: E402


async def check_and_create_admin():
    admin_email = os.environ.get("IBOOKS_ADMIN_EMAIL", "admin@example.com")
    admin_username = os.environ.get("IBOOKS_ADMIN_USERNAME", "admin")

    async with AsyncSessionLocal() as db:
        # Report only the aggregate count; avoid dumping user email addresses.
        result = await db.execute(select(func.count()).select_from(User))
        print(f"Total users found: {result.scalar_one()}")

        # Check for admin
        result = await db.execute(select(User).where(User.email == admin_email))
        admin = result.scalar_one_or_none()

        if not admin:
            admin_password = read_secret(
                "IBOOKS_ADMIN_PASSWORD",
                prompt="Admin password: ",
                confirmation_prompt="Confirm admin password: ",
            )
            print("\nCreating admin user...")
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
            print(f"✓ Created admin user: {admin_email}")
            print("  Password was supplied securely and was not printed.")
        else:
            print("\n✓ Admin user already exists.")


if __name__ == "__main__":
    asyncio.run(check_and_create_admin())

# -*- coding: utf-8 -*-
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


async def create_admin():
    from app.scripts.secure_inputs import read_secret
    from app.database import engine, init_db
    from app.models.user import User
    from app.utils.security import get_password_hash
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    admin_email = os.environ.get("IBOOKS_ADMIN_EMAIL", "admin@example.com")
    admin_username = os.environ.get("IBOOKS_ADMIN_USERNAME", "admin")
    admin_full_name = os.environ.get("IBOOKS_ADMIN_FULL_NAME", "Administrator")
    admin_password = read_secret(
        "IBOOKS_ADMIN_PASSWORD",
        prompt="Admin password: ",
        confirmation_prompt="Confirm admin password: ",
    )

    await init_db()

    async with AsyncSession(engine) as session:
        # 检查是否已存在 admin
        result = await session.execute(
            select(User).where(User.email == admin_email)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("Admin user already exists!")
            print(f"Email: {existing.email}")
            print(f"Username: {existing.username}")
            return

        # 创建管理员账�?
        admin = User(
            email=admin_email,
            username=admin_username,
            password_hash=get_password_hash(admin_password),
            full_name=admin_full_name,
            role="admin",
            status="active",
            is_email_verified=True,
        )

        session.add(admin)
        await session.commit()

        print("Admin user created successfully!")
        print(f"Email: {admin_email}")
        print("Password was supplied securely and was not printed.")


if __name__ == "__main__":
    asyncio.run(create_admin())

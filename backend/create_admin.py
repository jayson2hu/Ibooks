# -*- coding: utf-8 -*-
import asyncio
import sys

sys.path.insert(0, "D:/vscodefile/ibooks/backend")


async def create_admin():
    from app.database import engine, init_db
    from app.models.user import User
    from app.utils.security import get_password_hash
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    await init_db()

    async with AsyncSession(engine) as session:
        # 检查是否已存在 admin
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("Admin user already exists!")
            print(f"Email: {existing.email}")
            print(f"Username: {existing.username}")
            return

        # 创建管理员账�?
        admin = User(
            email="admin@example.com",
            username="admin",
            password_hash=get_password_hash("admin123"),
            full_name="Administrator",
            role="admin",
            status="active",
            is_email_verified=True,
        )

        session.add(admin)
        await session.commit()

        print("Admin user created successfully!")
        print("Email: admin@example.com")
        print("Password: admin123")
        print("Please change the password after first login!")


if __name__ == "__main__":
    asyncio.run(create_admin())

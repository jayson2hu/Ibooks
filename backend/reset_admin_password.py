# -*- coding: utf-8 -*-
import asyncio
import sys

sys.path.insert(0, "D:/vscodefile/ibooks/backend")


async def reset_password():
    from app.database import engine, init_db
    from app.models.user import User
    from app.utils.security import get_password_hash
    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import AsyncSession

    await init_db()

    async with AsyncSession(engine) as session:
        # 更新管理员密�?
        stmt = (
            update(User)
            .where(User.email == "admin@example.com")
            .values(password_hash=get_password_hash("admin123"))
        )
        await session.execute(stmt)
        await session.commit()

        print("Admin password reset successfully!")
        print("Email: admin@example.com")
        print("New Password: admin123")


if __name__ == "__main__":
    asyncio.run(reset_password())

# -*- coding: utf-8 -*-
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


async def reset_password():
    from app.scripts.secure_inputs import read_secret
    from app.database import engine, init_db
    from app.models.user import User
    from app.utils.security import get_password_hash
    from sqlalchemy import update
    from sqlalchemy.ext.asyncio import AsyncSession

    admin_email = os.environ.get("IBOOKS_ADMIN_EMAIL", "admin@example.com")
    admin_password = read_secret(
        "IBOOKS_ADMIN_PASSWORD",
        prompt="New admin password: ",
        confirmation_prompt="Confirm new admin password: ",
    )

    await init_db()

    async with AsyncSession(engine) as session:
        # 更新管理员密�?
        stmt = (
            update(User)
            .where(User.email == admin_email)
            .values(password_hash=get_password_hash(admin_password))
        )
        result = await session.execute(stmt)
        if result.rowcount == 0:
            await session.rollback()
            raise RuntimeError(f"Admin user not found: {admin_email}")
        await session.commit()

        print("Admin password reset successfully!")
        print(f"Email: {admin_email}")
        print("New password was supplied securely and was not printed.")


if __name__ == "__main__":
    asyncio.run(reset_password())

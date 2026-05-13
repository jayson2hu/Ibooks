# -*- coding: utf-8 -*-
import asyncio
import sys

sys.path.insert(0, 'D:/vscodefile/ibooks/backend')


async def update():
    from app.database import engine, init_db
    from sqlalchemy import text

    await init_db()

    copyright_val = '© 2024-2026 iBooks 站内大部分资源收集于网络，若侵犯了您的合法权益，请联系我们删除！'
    brand_val = '© 2016-2026 站内大部分资源收集于网络，若侵犯了您的合法权益，请联系我们删除！'

    async with engine.begin() as conn:
        await conn.execute(
            text('UPDATE site_settings SET value=:v WHERE key=:k'),
            {'v': copyright_val, 'k': 'copyright_text'}
        )
        await conn.execute(
            text('UPDATE site_settings SET value=:v WHERE key=:k'),
            {'v': brand_val, 'k': 'footer_brand_text'}
        )
        print('Settings updated successfully!')


if __name__ == "__main__":
    asyncio.run(update())

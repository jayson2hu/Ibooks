import asyncio
from app.database import get_db
from sqlalchemy import select
from app.models.category import Category
from app.models.site_settings import SiteSetting


async def check():
    async for db in get_db():
        # Check categories
        result = await db.execute(select(Category))
        cats = result.scalars().all()
        print(f"Categories count: {len(cats)}")
        for c in cats:
            print(f"  - {c.id}: {c.name} (parent_id: {c.parent_id})")

        # Check settings
        result = await db.execute(select(SiteSetting))
        settings = result.scalars().all()
        print(f"\nSettings count: {len(settings)}")
        for s in settings:
            print(f"  - {s.key}: {s.value[:50]}... (category: {s.category})")
        break


asyncio.run(check())

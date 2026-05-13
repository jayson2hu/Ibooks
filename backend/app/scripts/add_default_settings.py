"""
Script to add default site settings to the database.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.site_settings import SiteSetting


async def add_default_settings():
    """Add default site settings if they don't exist."""

    default_settings = [
        {
            "key": "copyright_text",
            "value": "Copyright 2016-2025. Contact us for takedown requests.",
            "category": "footer",
            "description": "Footer copyright text"
        },
        {
            "key": "site_name",
            "value": "Resource Marketplace",
            "category": "general",
            "description": "Website name"
        },
        {
            "key": "site_description",
            "value": "Curated ebooks, courses, and technical documents for learning and growth.",
            "category": "general",
            "description": "Website description"
        },
        {
            "key": "site_keywords",
            "value": "ebooks,courses,documents,resources",
            "category": "seo",
            "description": "SEO keywords"
        },
        {
            "key": "footer_brand_text",
            "value": "Curated digital resources for continuous learning.",
            "category": "footer",
            "description": "Footer brand description text"
        }
    ]

    async with AsyncSessionLocal() as db:
        for setting_data in default_settings:
            # Check if setting already exists
            result = await db.execute(
                select(SiteSetting).where(SiteSetting.key == setting_data["key"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                setting = SiteSetting(**setting_data)
                db.add(setting)
                print(f"Added setting: {setting_data['key']}")
            else:
                print(f"Setting already exists: {setting_data['key']}")

        await db.commit()
        print("Default settings configured successfully!")


if __name__ == "__main__":
    asyncio.run(add_default_settings())

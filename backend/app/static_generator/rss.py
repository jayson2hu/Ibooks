"""
RSS feed generation for blog/news.
"""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from feedgen.feed import FeedGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.resource import Resource


def _as_utc_aware(value: datetime) -> datetime:
    """Return a timezone-aware UTC value accepted by FeedGen."""
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def generate_rss_feed(db: AsyncSession, limit: int = 50) -> str:
    """
    Generate RSS feed for recent resources.
    
    Args:
        db: Database session
        limit: Number of recent items to include
    
    Returns:
        RSS XML string
    """
    # Create feed generator
    fg = FeedGenerator()
    fg.id(settings.SITE_URL)
    fg.title(settings.APP_NAME)
    fg.link(href=settings.SITE_URL, rel='alternate')
    fg.link(href=f"{settings.SITE_URL}/rss.xml", rel='self')
    fg.description(f'Latest resources from {settings.APP_NAME}')
    fg.language('zh-CN')
    
    # Get recent resources
    result = await db.execute(
        select(Resource)
        .options(selectinload(Resource.category))
        .where(Resource.is_published)
        .order_by(Resource.published_at.desc())
        .limit(limit)
    )
    resources = result.scalars().all()
    
    # Add entries
    for resource in resources:
        fe = fg.add_entry()
        fe.id(f"{settings.SITE_URL}/resources/{resource.slug}")
        fe.title(resource.title)
        fe.link(href=f"{settings.SITE_URL}/resources/{resource.slug}")
        
        if resource.description:
            fe.description(resource.description)
        elif resource.excerpt:
            fe.description(resource.excerpt)
        
        if resource.published_at:
            fe.published(_as_utc_aware(resource.published_at))
        
        fe.updated(_as_utc_aware(resource.updated_at))
        
        # Add categories
        if resource.category:
            fe.category(term=resource.category.name)
        
        # Add author (can be customized)
        fe.author(name=settings.APP_NAME)
    
    return fg.rss_str(pretty=True).decode('utf-8')


def _write_rss_feed(output_path: str | Path, rss_xml: str) -> str:
    """Write an RSS feed on a worker thread and return its resolved path."""
    destination = Path(output_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rss_xml, encoding="utf-8")
    return str(destination)


async def save_rss_feed(
    db: AsyncSession,
    output_path: str | Path | None = None,
    limit: int = 50,
):
    """
    Generate and save RSS feed to file.
    
    Args:
        db: Database session
        output_path: Path to save RSS feed
        limit: Number of items to include
    """
    if output_path is None:
        output_path = f"{settings.STATIC_PAGES_DIR}/rss.xml"
    
    rss_xml = await generate_rss_feed(db, limit)
    
    return await asyncio.to_thread(_write_rss_feed, output_path, rss_xml)

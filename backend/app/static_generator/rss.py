"""
RSS feed generation for blog/news.
"""
from datetime import datetime
from feedgen.feed import FeedGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.resource import Resource
from app.config import settings


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
        .where(Resource.is_published == True)
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
            fe.published(resource.published_at)
        
        fe.updated(resource.updated_at)
        
        # Add categories
        if resource.category:
            fe.category(term=resource.category.name)
        
        # Add author (can be customized)
        fe.author(name=settings.APP_NAME)
    
    return fg.rss_str(pretty=True).decode('utf-8')


async def save_rss_feed(db: AsyncSession, output_path: str = None, limit: int = 50):
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
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rss_xml)
    
    return output_path

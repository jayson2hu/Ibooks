"""
Sitemap XML generation for SEO.
"""
import asyncio
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.resource import Resource
from app.models.category import Category
from app.config import settings
from app.utils.datetime_utils import utc_now


async def generate_sitemap_xml(db: AsyncSession) -> str:
    """
    Generate sitemap.xml for search engines.
    
    Args:
        db: Database session
    
    Returns:
        Formatted XML string
    """
    # Create root element
    urlset = Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    # Add homepage
    add_url_to_sitemap(
        urlset,
        url=settings.SITE_URL,
        lastmod=utc_now(),
        changefreq='daily',
        priority='1.0'
    )
    
    # Add resources
    result = await db.execute(
        select(Resource).where(Resource.is_published)
    )
    resources = result.scalars().all()
    
    for resource in resources:
        add_url_to_sitemap(
            urlset,
            url=f"{settings.SITE_URL}/resources/{resource.slug}",
            lastmod=resource.updated_at,
            changefreq='weekly',
            priority='0.8'
        )
    
    # Add categories
    result = await db.execute(
        select(Category).where(Category.is_active)
    )
    categories = result.scalars().all()
    
    for category in categories:
        add_url_to_sitemap(
            urlset,
            url=f"{settings.SITE_URL}/categories/{category.slug}",
            lastmod=category.updated_at,
            changefreq='weekly',
            priority='0.6'
        )
    
    # Add static pages
    static_pages = [
        {'url': '/about', 'priority': '0.5'},
        {'url': '/contact', 'priority': '0.5'},
        {'url': '/search', 'priority': '0.4'},
    ]
    
    for page in static_pages:
        add_url_to_sitemap(
            urlset,
            url=f"{settings.SITE_URL}{page['url']}",
            lastmod=utc_now(),
            changefreq='monthly',
            priority=page['priority']
        )
    
    # Convert to pretty XML string
    rough_string = tostring(urlset, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def add_url_to_sitemap(
    urlset: Element,
    url: str,
    lastmod: datetime,
    changefreq: str,
    priority: str
):
    """Add a URL entry to the sitemap."""
    url_element = SubElement(urlset, 'url')
    
    loc = SubElement(url_element, 'loc')
    loc.text = url
    
    lastmod_element = SubElement(url_element, 'lastmod')
    lastmod_element.text = lastmod.strftime('%Y-%m-%d')
    
    changefreq_element = SubElement(url_element, 'changefreq')
    changefreq_element.text = changefreq
    
    priority_element = SubElement(url_element, 'priority')
    priority_element.text = priority


def _write_sitemap(output_path: str | Path, sitemap_xml: str) -> str:
    """Write a sitemap on a worker thread and return its resolved path."""
    destination = Path(output_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(sitemap_xml, encoding="utf-8")
    return str(destination)


async def save_sitemap(db: AsyncSession, output_path: str | Path | None = None):
    """
    Generate and save sitemap to file.
    
    Args:
        db: Database session
        output_path: Path to save sitemap (default: static_pages_dir/sitemap.xml)
    """
    if output_path is None:
        output_path = f"{settings.STATIC_PAGES_DIR}/sitemap.xml"
    
    sitemap_xml = await generate_sitemap_xml(db)
    
    return await asyncio.to_thread(_write_sitemap, output_path, sitemap_xml)

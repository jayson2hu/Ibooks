"""
Robots.txt generation for SEO.
"""
from pathlib import Path

from app.config import settings


def generate_robots_txt() -> str:
    """
    Generate robots.txt content.
    
    Returns:
        robots.txt content as string
    """
    robots_content = f"""# robots.txt for {settings.APP_NAME}

User-agent: *
Allow: /

# Sitemap
Sitemap: {settings.SITE_URL}/sitemap.xml

# Disallow admin and private areas
Disallow: /admin/
Disallow: /api/
Disallow: /private/

# Crawl-delay for polite crawlers
User-agent: Googlebot
Crawl-delay: 0

User-agent: Baiduspider
Crawl-delay: 1

User-agent: Sogou web spider
Crawl-delay: 2
"""
    return robots_content


def save_robots_txt(output_path: str | Path | None = None):
    """
    Generate and save robots.txt to file.
    
    Args:
        output_path: Path to save robots.txt
    """
    if output_path is None:
        output_path = f"{settings.STATIC_PAGES_DIR}/robots.txt"
    
    robots_content = generate_robots_txt()
    
    destination = Path(output_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(robots_content, encoding="utf-8")

    return str(destination)

"""
Static generator package.
"""
from app.static_generator.sitemap import generate_sitemap_xml, save_sitemap
from app.static_generator.rss import generate_rss_feed, save_rss_feed
from app.static_generator.robots import generate_robots_txt, save_robots_txt
from app.static_generator.html_generator import generate_resource_html, save_resource_html

__all__ = [
    "generate_sitemap_xml",
    "save_sitemap",
    "generate_rss_feed",
    "save_rss_feed",
    "generate_robots_txt",
    "save_robots_txt",
    "generate_resource_html",
    "save_resource_html",
]

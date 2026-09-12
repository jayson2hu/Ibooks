"""
HTML page generation for static SEO pages.
"""
import re
from pathlib import Path

from jinja2 import Environment, select_autoescape
from typing import Dict, Any
from app.config import settings


RESOURCE_SLUG_MAX_LENGTH = 200
_RESOURCE_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_HTML_ENVIRONMENT = Environment(
    autoescape=select_autoescape(default_for_string=True, default=True),
)


def is_valid_resource_slug(slug: str) -> bool:
    """Return whether a slug matches the format produced by ``generate_slug``."""
    return (
        isinstance(slug, str)
        and bool(slug)
        and len(slug) <= RESOURCE_SLUG_MAX_LENGTH
        and _RESOURCE_SLUG_PATTERN.fullmatch(slug) is not None
    )


def get_resource_html_path(
    slug: str,
    static_pages_dir: str | Path | None = None,
) -> Path:
    """Resolve a generated resource page without allowing path traversal."""
    if not is_valid_resource_slug(slug):
        raise ValueError("Invalid resource slug")

    configured_dir = (
        settings.STATIC_PAGES_DIR
        if static_pages_dir is None
        else static_pages_dir
    )
    static_root = Path(configured_dir).expanduser().resolve()
    resources_dir = (static_root / "resources").resolve()
    if resources_dir.parent != static_root:
        raise ValueError("Invalid generated resources directory")

    output_path = (resources_dir / f"{slug}.html").resolve()
    if output_path.parent != resources_dir:
        raise ValueError("Invalid generated resource path")
    return output_path


# HTML template for resource detail page
RESOURCE_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ meta_title or title }} - {{ site_name }}</title>
    <meta name="description" content="{{ meta_description or excerpt }}">
    <meta name="keywords" content="{{ meta_keywords }}">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{{ title }}">
    <meta property="og:description" content="{{ meta_description or excerpt }}">
    <meta property="og:image" content="{{ cover_image_url }}">
    <meta property="og:url" content="{{ url }}">
    <meta property="og:type" content="product">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ title }}">
    <meta name="twitter:description" content="{{ meta_description or excerpt }}">
    <meta name="twitter:image" content="{{ cover_image_url }}">
    
    <!-- JSON-LD -->
    <script type="application/ld+json">{{ json_ld | tojson }}</script>
    
    <!-- Canonical URL -->
    <link rel="canonical" href="{{ url }}">
</head>
<body>
    <h1>{{ title }}</h1>
    <div class="description">{{ description }}</div>
    <div class="price">¥{{ price }}</div>
    
    <!-- This is a static SEO page, actual content loaded by frontend -->
    <noscript>
        <p>请启用 JavaScript 以获得完整体验</p>
    </noscript>
</body>
</html>
"""


def generate_resource_html(resource_data: Dict[str, Any]) -> str:
    """
    Generate static HTML for a resource page.
    
    Args:
        resource_data: Dictionary containing resource information
    
    Returns:
        HTML string
    """
    title = resource_data.get('title') or ''
    description = resource_data.get('description') or ''
    cover_image_url = resource_data.get('cover_image_url') or ''
    price = resource_data.get('price', 0)
    slug = resource_data.get('slug') or ''
    url = f"{settings.SITE_URL}/resources/{slug}"
    template = _HTML_ENVIRONMENT.from_string(RESOURCE_TEMPLATE)

    html = template.render(
        title=title,
        description=description,
        excerpt=resource_data.get('excerpt') or '',
        meta_title=resource_data.get('meta_title'),
        meta_description=resource_data.get('meta_description'),
        meta_keywords=resource_data.get('meta_keywords') or '',
        cover_image_url=cover_image_url,
        price=price,
        url=url,
        site_name=settings.APP_NAME,
        json_ld={
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": title,
            "description": description,
            "image": cover_image_url,
            "url": url,
            "offers": {
                "@type": "Offer",
                "price": str(price),
                "priceCurrency": "CNY",
                "availability": "https://schema.org/InStock",
            },
        },
    )
    
    return html


def save_resource_html(
    resource_data: Dict[str, Any],
    output_path: str | Path | None = None,
):
    """
    Generate and save resource HTML to file.
    
    Args:
        resource_data: Resource information
        output_path: Path to save HTML file
    """
    slug = resource_data.get('slug') or 'resource'
    if not is_valid_resource_slug(slug):
        raise ValueError("Invalid resource slug")

    destination = (
        get_resource_html_path(slug)
        if output_path is None
        else Path(output_path).expanduser()
    )
    
    html = generate_resource_html(resource_data)
    
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding='utf-8')
    
    return str(destination)

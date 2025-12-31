"""
HTML page generation for static SEO pages.
"""
from jinja2 import Template
from typing import Dict, Any
from app.config import settings


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
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "{{ title }}",
        "description": "{{ description }}",
        "image": "{{ cover_image_url }}",
        "url": "{{ url }}",
        "offers": {
            "@type": "Offer",
            "price": "{{ price }}",
            "priceCurrency": "CNY",
            "availability": "https://schema.org/InStock"
        }
    }
    </script>
    
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
    template = Template(RESOURCE_TEMPLATE)
    
    html = template.render(
        title=resource_data.get('title', ''),
        description=resource_data.get('description', ''),
        excerpt=resource_data.get('excerpt', ''),
        meta_title=resource_data.get('meta_title'),
        meta_description=resource_data.get('meta_description'),
        meta_keywords=resource_data.get('meta_keywords', ''),
        cover_image_url=resource_data.get('cover_image_url', ''),
        price=resource_data.get('price', 0),
        url=f"{settings.SITE_URL}/resources/{resource_data.get('slug', '')}",
        site_name=settings.APP_NAME
    )
    
    return html


def save_resource_html(resource_data: Dict[str, Any], output_path: str = None):
    """
    Generate and save resource HTML to file.
    
    Args:
        resource_data: Resource information
        output_path: Path to save HTML file
    """
    if output_path is None:
        slug = resource_data.get('slug', 'resource')
        output_path = f"{settings.STATIC_PAGES_DIR}/resources/{slug}.html"
    
    html = generate_resource_html(resource_data)
    
    # Ensure directory exists
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path

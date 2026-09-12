"""
SEO utilities for URL slugs, meta tags, and structured data.
"""
from slugify import slugify
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings
from app.utils.logging import get_logger


logger = get_logger(__name__)


def generate_slug(text: str, max_length: int = 200) -> str:
    """
    Generate SEO-friendly URL slug from text.
    
    Args:
        text: Text to convert to slug
        max_length: Maximum length of slug
    
    Returns:
        URL-safe slug
    """
    slug = slugify(text, max_length=max_length)
    return slug


def generate_meta_tags(
    title: str,
    description: str,
    keywords: Optional[List[str]] = None,
    image_url: Optional[str] = None,
    url: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate meta tags for SEO.
    
    Args:
        title: Page title
        description: Page description
        keywords: List of keywords
        image_url: OG image URL
        url: Canonical URL
    
    Returns:
        Dictionary of meta tags
    """
    meta_tags = {
        "title": title,
        "description": description,
    }
    
    if keywords:
        meta_tags["keywords"] = ", ".join(keywords)
    
    # Open Graph tags
    if image_url:
        meta_tags["og:image"] = image_url
    
    if url:
        meta_tags["og:url"] = url
        meta_tags["canonical"] = url
    
    meta_tags["og:title"] = title
    meta_tags["og:description"] = description
    meta_tags["og:type"] = "website"
    
    # Twitter Card tags
    meta_tags["twitter:card"] = "summary_large_image"
    meta_tags["twitter:title"] = title
    meta_tags["twitter:description"] = description
    if image_url:
        meta_tags["twitter:image"] = image_url
    
    return meta_tags


def generate_product_json_ld(
    name: str,
    description: str,
    image_url: str,
    price: float,
    currency: str = "CNY",
    url: Optional[str] = None,
    availability: str = "https://schema.org/InStock"
) -> Dict[str, Any]:
    """
    Generate JSON-LD structured data for product.
    
    Args:
        name: Product name
        description: Product description
        image_url: Product image URL
        price: Product price
        currency: Currency code
        url: Product URL
        availability: Availability status
    
    Returns:
        JSON-LD structured data dictionary
    """
    json_ld = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": name,
        "description": description,
        "image": image_url,
        "offers": {
            "@type": "Offer",
            "price": str(price),
            "priceCurrency": currency,
            "availability": availability,
        }
    }
    
    if url:
        json_ld["url"] = url
        json_ld["offers"]["url"] = url
    
    return json_ld


def generate_breadcrumb_json_ld(breadcrumbs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generate JSON-LD structured data for breadcrumbs.
    
    Args:
        breadcrumbs: List of breadcrumb items [{"name": "Home", "url": "/"}]
    
    Returns:
        JSON-LD structured data dictionary
    """
    items = []
    for i, crumb in enumerate(breadcrumbs, start=1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "name": crumb["name"],
            "item": crumb["url"]
        })
    
    return {
        "@context": "https://schema.org/",
        "@type": "BreadcrumbList",
        "itemListElement": items
    }


def generate_website_json_ld(
    name: str,
    url: str,
    description: str,
    search_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate JSON-LD structured data for website.
    
    Args:
        name: Website name
        url: Website URL
        description: Website description
        search_url: Search URL template
    
    Returns:
        JSON-LD structured data dictionary
    """
    json_ld = {
        "@context": "https://schema.org/",
        "@type": "WebSite",
        "name": name,
        "url": url,
        "description": description,
    }
    
    if search_url:
        json_ld["potentialAction"] = {
            "@type": "SearchAction",
            "target": search_url,
            "query-input": "required name=search_term_string"
        }
    
    return json_ld


async def push_to_baidu(urls: list[str]) -> Dict[str, Any]:
    """Submit indexable URLs to Baidu when SEO submission is configured."""
    cleaned_urls = list(dict.fromkeys(url.strip() for url in urls if url and url.strip()))
    if not settings.SEO_SUBMIT_BAIDU or not settings.BAIDU_API_KEY or not cleaned_urls:
        logger.info(
            "Baidu URL submission skipped",
            extra={
                "enabled": settings.SEO_SUBMIT_BAIDU,
                "has_api_key": bool(settings.BAIDU_API_KEY),
                "url_count": len(cleaned_urls),
            },
        )
        return {"skipped": True, "submitted": 0}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://data.zz.baidu.com/urls",
            params={"site": settings.SITE_URL, "token": settings.BAIDU_API_KEY},
            content="\n".join(cleaned_urls),
            headers={"Content-Type": "text/plain"},
        )
        response.raise_for_status()
        result = response.json()

    if isinstance(result, dict):
        result.setdefault("submitted", len(cleaned_urls))
        logger.info(
            "Baidu URL submission completed",
            extra={
                "submitted_count": result.get("submitted", len(cleaned_urls)),
                "success_count": result.get("success"),
                "remaining_quota": result.get("remain"),
            },
        )
    return result

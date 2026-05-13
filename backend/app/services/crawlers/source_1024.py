"""
Metadata crawler for https://www.1024zyz.com/.

The implementation only reads publicly visible listing metadata and source links.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from html import unescape
import re

import httpx


ARTICLE_PATTERN = re.compile(
    r"<article\b[^>]*id=[\"']post-(?P<post_id>\d+)[\"'][^>]*>(?P<body>.*?)</article>",
    re.IGNORECASE | re.DOTALL,
)
TITLE_PATTERN = re.compile(
    r'<h2 class="entry-title">\s*<a[^>]*href=[\"\'](?P<url>[^\"\']+)[\"\'][^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
EXCERPT_PATTERN = re.compile(
    r'<div class="entry-excerpt">(?P<excerpt>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
CATEGORY_PATTERN = re.compile(
    r'<span class="meta-category-dot">.*?<a[^>]*>(?P<category>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TIME_PATTERN = re.compile(
    r"<time[^>]*datetime=[\"\'](?P<datetime>[^\"\']+)[\"\']",
    re.IGNORECASE | re.DOTALL,
)
IMAGE_DATA_SRC_PATTERN = re.compile(
    r"<img[^>]*\bdata-src=[\"\'](?P<image>[^\"\']+)[\"\']",
    re.IGNORECASE | re.DOTALL,
)
IMAGE_SRC_PATTERN = re.compile(
    r"<img[^>]*\bsrc=[\"\'](?P<image>[^\"\']+)[\"\']",
    re.IGNORECASE | re.DOTALL,
)
TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")
POST_ID_FROM_URL_PATTERN = re.compile(r"/(?P<post_id>\d+)\.html?$", re.IGNORECASE)

CRAWLER_FIELD_OPTIONS = [
    {
        "key": "title",
        "label": "Title",
        "description": "Resource title parsed from the listing card.",
        "required": True,
    },
    {
        "key": "source_url",
        "label": "Source URL",
        "description": "Original detail page URL used for deduplication and traceability.",
        "required": True,
    },
    {
        "key": "external_id",
        "label": "External ID",
        "description": "Stable identifier extracted from the listing URL.",
        "required": True,
    },
    {
        "key": "excerpt",
        "label": "Excerpt",
        "description": "Short description parsed from the listing page.",
        "required": False,
    },
    {
        "key": "cover_image_url",
        "label": "Cover Image",
        "description": "Image URL parsed from the listing page.",
        "required": False,
    },
    {
        "key": "resource_type",
        "label": "Resource Type",
        "description": "Category label parsed from the listing page.",
        "required": False,
    },
    {
        "key": "external_published_at",
        "label": "Published At",
        "description": "Publication timestamp parsed from the listing page.",
        "required": False,
    },
    {
        "key": "tags",
        "label": "Tags",
        "description": "Tags composed from source and category metadata.",
        "required": False,
    },
]


@dataclass
class ExternalResourceCandidate:
    """Normalized listing metadata produced by the crawler."""

    external_id: str
    title: str
    source_url: str
    excerpt: str | None = None
    cover_image_url: str | None = None
    resource_type: str | None = None
    external_published_at: datetime | None = None
    tags: list[str] = field(default_factory=list)


class Source1024Crawler:
    """Crawler for the public 1024zyz.com listing pages."""

    BASE_URL = "https://www.1024zyz.com"
    SOURCE_SITE = "1024zyz.com"

    def __init__(self, *, timeout_seconds: int = 15) -> None:
        self.timeout_seconds = timeout_seconds
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; iBooksMetadataBot/1.0; "
                "+https://www.1024zyz.com/)"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    async def crawl(self, *, max_pages: int = 2) -> list[ExternalResourceCandidate]:
        """Fetch and parse a number of public listing pages."""
        items: list[ExternalResourceCandidate] = []
        seen_keys: set[str] = set()

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers=self.headers,
        ) as client:
            for page in range(1, max_pages + 1):
                page_url = self._build_page_url(page)
                response = await client.get(page_url)
                response.raise_for_status()

                for candidate in self.parse_listing_page(response.text):
                    dedupe_key = f"{candidate.external_id}:{candidate.source_url}"
                    if dedupe_key in seen_keys:
                        continue
                    seen_keys.add(dedupe_key)
                    items.append(candidate)

        return items

    @classmethod
    def parse_listing_page(cls, html: str) -> list[ExternalResourceCandidate]:
        """Parse a listing page into normalized metadata."""
        candidates: list[ExternalResourceCandidate] = []

        for match in ARTICLE_PATTERN.finditer(html):
            post_id = match.group("post_id")
            body = match.group("body")

            title_match = TITLE_PATTERN.search(body)
            if not title_match:
                continue

            source_url = title_match.group("url").strip()
            external_id = cls._extract_external_id(post_id, source_url)
            title = cls._clean_text(title_match.group("title"))
            excerpt = cls._extract_optional_text(EXCERPT_PATTERN, body)
            category = cls._extract_optional_text(CATEGORY_PATTERN, body)
            published_at = cls._parse_datetime(TIME_PATTERN.search(body))
            cover_image_url = cls._extract_image_url(body)

            tags = ["1024 resources", "external source"]
            if category:
                tags.insert(0, category)

            candidates.append(
                ExternalResourceCandidate(
                    external_id=external_id,
                    title=title,
                    source_url=source_url,
                    excerpt=excerpt,
                    cover_image_url=cover_image_url,
                    resource_type=category or "external_resource",
                    external_published_at=published_at,
                    tags=list(dict.fromkeys(tags)),
                )
            )

        return candidates

    @classmethod
    def _build_page_url(cls, page: int) -> str:
        if page <= 1:
            return f"{cls.BASE_URL}/"
        return f"{cls.BASE_URL}/page/{page}/"

    @staticmethod
    def _extract_external_id(fallback_post_id: str, source_url: str) -> str:
        match = POST_ID_FROM_URL_PATTERN.search(source_url)
        if match:
            return match.group("post_id")
        return fallback_post_id

    @staticmethod
    def _extract_optional_text(pattern: re.Pattern[str], body: str) -> str | None:
        match = pattern.search(body)
        if not match:
            return None
        return Source1024Crawler._clean_text(next(iter(match.groupdict().values())))

    @staticmethod
    def _extract_image_url(body: str) -> str | None:
        for pattern in (IMAGE_DATA_SRC_PATTERN, IMAGE_SRC_PATTERN):
            match = pattern.search(body)
            if not match:
                continue
            image_url = match.group("image").strip()
            if "thumb-ing.gif" in image_url:
                continue
            return image_url
        return None

    @staticmethod
    def _clean_text(value: str) -> str:
        no_tags = TAG_PATTERN.sub(" ", value)
        normalized = WHITESPACE_PATTERN.sub(" ", unescape(no_tags)).strip()
        return normalized

    @staticmethod
    def _parse_datetime(match: re.Match[str] | None) -> datetime | None:
        if not match:
            return None

        raw_value = match.group("datetime").strip()
        try:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        except ValueError:
            return None

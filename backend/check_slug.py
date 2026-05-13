"""Check for duplicate slugs in crawled data."""
import asyncio
import httpx
import sys
sys.path.insert(0, '.')

from app.services.crawlers.source_1024 import Source1024Crawler
from app.utils.seo import generate_slug

async def main():
    crawler = Source1024Crawler(timeout_seconds=15)
    candidates = await crawler.crawl(max_pages=2)

    slug_map = {}
    for c in candidates:
        slug = generate_slug(c.title) or f"external-resource-{c.external_id}"
        if slug in slug_map:
            print(f"\n*** DUPLICATE SLUG: {slug}")
            print(f"  Entry 1: id={slug_map[slug].external_id}, title={slug_map[slug].title}")
            print(f"  Entry 2: id={c.external_id}, title={c.title}")
        else:
            slug_map[slug] = c

    print(f"\nTotal candidates: {len(candidates)}")
    print(f"Unique slugs: {len(slug_map)}")
    print(f"Duplicates found: {len(candidates) - len(slug_map)}")

asyncio.run(main())

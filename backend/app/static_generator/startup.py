"""Best-effort generation of local SEO artifacts during application startup."""
import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.config import settings
from app.database import AsyncSessionLocal
from app.static_generator.robots import save_robots_txt
from app.static_generator.rss import save_rss_feed
from app.static_generator.sitemap import save_sitemap


logger = logging.getLogger(__name__)


async def _generate_sitemap() -> None:
    """Generate the sitemap with a session scoped only to this startup read."""
    async with AsyncSessionLocal() as db:
        await save_sitemap(db)


async def _generate_rss() -> None:
    """Generate the RSS feed with a session scoped only to this startup read."""
    async with AsyncSessionLocal() as db:
        await save_rss_feed(db)


async def _generate_robots() -> None:
    """Move the synchronous robots.txt write off the event loop."""
    await asyncio.to_thread(save_robots_txt)


async def generate_startup_seo_files() -> bool:
    """Generate local SEO files without submitting URLs to external services.

    Generation is deliberately best effort: a database or filesystem failure is
    recorded without including exception text, and application startup can
    continue. Each artifact is attempted independently so one failure does not
    prevent the remaining local files from being refreshed.
    """
    if not settings.SEO_AUTO_GENERATE:
        logger.info(
            "Automatic SEO artifact generation is disabled",
            extra={"event": "seo_startup_generation_skipped"},
        )
        return False

    generators: tuple[tuple[str, Callable[[], Awaitable[None]]], ...] = (
        ("sitemap.xml", _generate_sitemap),
        ("rss.xml", _generate_rss),
        ("robots.txt", _generate_robots),
    )
    failures: list[tuple[str, str]] = []

    for artifact, generate in generators:
        try:
            await generate()
        except Exception as exc:
            failures.append((artifact, type(exc).__name__))

    if failures:
        logger.error(
            "Automatic SEO artifact generation was incomplete; startup will continue",
            extra={
                "event": "seo_startup_generation_failed",
                "failed_artifacts": [artifact for artifact, _ in failures],
                "error_types": [error_type for _, error_type in failures],
            },
        )
        return False

    logger.info(
        "Automatic SEO artifacts generated",
        extra={
            "event": "seo_startup_generation_completed",
            "artifact_count": len(generators),
        },
    )
    return True

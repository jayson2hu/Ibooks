"""
SEO management endpoints for generating sitemap, RSS, etc.
"""
import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import List
from xml.etree.ElementTree import parse

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.dependencies import get_current_staff
from app.models.resource import Resource
from app.schemas.common import Message
from app.static_generator import (
    save_resource_html,
    save_robots_txt,
    save_rss_feed,
    save_sitemap,
)
from app.utils.seo import push_to_baidu


router = APIRouter(prefix="/seo", tags=["SEO"])
logger = logging.getLogger(__name__)


class URLSubmissionRequest(BaseModel):
    """URLs to submit to configured search engine services."""
    urls: List[HttpUrl] = Field(..., min_length=1, max_length=200)


class SEOGenerationResponse(BaseModel):
    """Result returned after every requested SEO artifact is safely persisted."""

    message: str
    generated: list[str]


def _read_sitemap_urls(sitemap_path: str) -> list[str]:
    """Read sitemap URLs away from the event loop."""
    root = parse(Path(sitemap_path)).getroot()
    return [
        element.text
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "loc" and element.text
    ]


async def _generate_sitemap_and_submit(db):
    """Generate the sitemap and optionally submit its URLs to Baidu."""
    sitemap_path = await save_sitemap(db)
    if not settings.SEO_SUBMIT_BAIDU or not settings.BAIDU_API_KEY or not sitemap_path:
        return

    urls = await asyncio.to_thread(_read_sitemap_urls, sitemap_path)
    await push_to_baidu(urls)


async def _generate_sitemap_artifact() -> None:
    """Generate the sitemap with a request-scoped database session."""
    async with AsyncSessionLocal() as db:
        await _generate_sitemap_and_submit(db)


async def _generate_rss_artifact() -> None:
    """Generate RSS with a request-scoped database session."""
    async with AsyncSessionLocal() as db:
        await save_rss_feed(db)


async def _generate_robots_artifact() -> None:
    """Move the synchronous robots.txt write off the event loop."""
    await asyncio.to_thread(save_robots_txt)


@router.post("/submit-baidu")
async def submit_baidu(
    payload: URLSubmissionRequest,
    current_user=Depends(get_current_staff),
):
    """Submit URLs to Baidu; returns skipped when integration is disabled."""
    try:
        return await push_to_baidu([str(url) for url in payload.urls])
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Baidu URL submission failed",
        ) from exc


@router.post("/generate-sitemap", response_model=Message)
async def generate_sitemap(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_staff)
):
    """
    Generate sitemap.xml (Admin only).
    
    This is run in the background.
    """
    async def generate_task():
        async with AsyncSessionLocal() as db:
            await _generate_sitemap_and_submit(db)
    
    background_tasks.add_task(generate_task)
    
    return {"message": "Sitemap generation started"}


@router.post("/generate-rss", response_model=Message)
async def generate_rss(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_staff)
):
    """
    Generate RSS feed (Admin only).
    
    This is run in the background.
    """
    async def generate_task():
        async with AsyncSessionLocal() as db:
            await save_rss_feed(db)
    
    background_tasks.add_task(generate_task)
    
    return {"message": "RSS feed generation started"}


@router.post("/generate-robots", response_model=Message)
async def generate_robots(
    current_user = Depends(get_current_staff)
):
    """Generate robots.txt (Admin only)."""
    save_robots_txt()
    return {"message": "robots.txt generated successfully"}


@router.post("/generate-all", response_model=SEOGenerationResponse)
async def generate_all(
    current_user=Depends(get_current_staff),
):
    """Generate all SEO files and return only after their outcome is known."""
    generators: tuple[tuple[str, Callable[[], Awaitable[None]]], ...] = (
        ("sitemap.xml", _generate_sitemap_artifact),
        ("rss.xml", _generate_rss_artifact),
        ("robots.txt", _generate_robots_artifact),
    )
    generated: list[str] = []
    failures: list[tuple[str, str]] = []

    for artifact, generate in generators:
        try:
            await generate()
            generated.append(artifact)
        except Exception as exc:
            failures.append((artifact, type(exc).__name__))

    if failures:
        failed_artifacts = [artifact for artifact, _ in failures]
        logger.error(
            "Administrator SEO artifact generation was incomplete",
            extra={
                "event": "seo_admin_generation_failed",
                "generated_artifacts": generated,
                "failed_artifacts": failed_artifacts,
                "error_types": [error_type for _, error_type in failures],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "部分 SEO 文件生成失败，请重试",
                "generated": generated,
                "failed": failed_artifacts,
            },
        )

    logger.info(
        "Administrator SEO artifacts generated",
        extra={
            "event": "seo_admin_generation_completed",
            "generated_artifacts": generated,
        },
    )
    return {
        "message": "SEO 文件生成完成",
        "generated": generated,
    }


@router.post("/generate-static-pages", response_model=Message)
async def generate_static_pages(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_staff)
):
    """
    Generate static HTML pages for all resources (Admin only).
    
    This is run in the background.
    """
    async def generate_task():
        async with AsyncSessionLocal() as db:
            # Get all published resources
            result = await db.execute(
                select(Resource).where(Resource.is_published)
            )
            resources = result.scalars().all()
            
            # Generate HTML for each resource
            for resource in resources:
                resource_data = {
                    'title': resource.title,
                    'slug': resource.slug,
                    'description': resource.description,
                    'excerpt': resource.excerpt,
                    'meta_title': resource.meta_title,
                    'meta_description': resource.meta_description,
                    'meta_keywords': resource.meta_keywords,
                    'cover_image_url': resource.cover_image_url,
                    'price': float(resource.price),
                }
                save_resource_html(resource_data)
    
    background_tasks.add_task(generate_task)
    
    return {"message": "Static page generation started"}

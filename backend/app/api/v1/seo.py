"""
SEO management endpoints for generating sitemap, RSS, etc.
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.common import Message
from app.static_generator import (
    save_sitemap,
    save_rss_feed,
    save_robots_txt,
    save_resource_html
)
from app.models.resource import Resource
from sqlalchemy import select


router = APIRouter(prefix="/seo", tags=["SEO"])


@router.post("/generate-sitemap", response_model=Message)
async def generate_sitemap(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Generate sitemap.xml (Admin only).
    
    This is run in the background.
    """
    async def generate_task():
        await save_sitemap(db)
    
    background_tasks.add_task(generate_task)
    
    return {"message": "Sitemap generation started"}


@router.post("/generate-rss", response_model=Message)
async def generate_rss(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Generate RSS feed (Admin only).
    
    This is run in the background.
    """
    async def generate_task():
        await save_rss_feed(db)
    
    background_tasks.add_task(generate_task)
    
    return {"message": "RSS feed generation started"}


@router.post("/generate-robots", response_model=Message)
async def generate_robots(
    current_user = Depends(get_current_admin)
):
    """Generate robots.txt (Admin only)."""
    save_robots_txt()
    return {"message": "robots.txt generated successfully"}


@router.post("/generate-all", response_model=Message)
async def generate_all(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Generate all SEO files (sitemap, RSS, robots.txt) (Admin only).
    
    This is run in the background.
    """
    async def generate_all_task():
        await save_sitemap(db)
        await save_rss_feed(db)
        save_robots_txt()
    
    background_tasks.add_task(generate_all_task)
    
    return {"message": "SEO file generation started"}


@router.post("/generate-static-pages", response_model=Message)
async def generate_static_pages(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Generate static HTML pages for all resources (Admin only).
    
    This is run in the background.
    """
    async def generate_task():
        # Get all published resources
        result = await db.execute(
            select(Resource).where(Resource.is_published == True)
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

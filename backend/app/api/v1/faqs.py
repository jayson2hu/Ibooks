"""
FAQ endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.dependencies import get_current_staff
from app.schemas.faq import FAQCreate, FAQUpdate, FAQResponse
from app.schemas.common import Message
from app.models.faq import FAQ


router = APIRouter(prefix="/faqs", tags=["FAQs"])


@router.get("", response_model=List[FAQResponse])
async def list_faqs(
    active_only: bool = True,
    category: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all FAQs.
    
    - **active_only**: Only return active FAQs (default: True)
    - **category**: Filter by category
    """
    query = select(FAQ).order_by(FAQ.category, FAQ.display_order)
    
    if active_only:
        query = query.where(FAQ.is_active)
    
    if category:
        query = query.where(FAQ.category == category)
    
    result = await db.execute(query)
    faqs = result.scalars().all()
    
    return faqs


@router.get("/{faq_id}", response_model=FAQResponse)
async def get_faq(faq_id: int, db: AsyncSession = Depends(get_db)):
    """Get FAQ by ID."""
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found"
        )
    
    return faq


@router.post("", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    faq_data: FAQCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_staff)
):
    """Create a new FAQ (Admin only)."""
    new_faq = FAQ(**faq_data.model_dump())
    
    db.add(new_faq)
    await db.commit()
    await db.refresh(new_faq)
    
    return new_faq


@router.patch("/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: int,
    faq_data: FAQUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_staff)
):
    """Update a FAQ (Admin only)."""
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found"
        )
    
    # Update fields
    update_data = faq_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(faq, field, value)
    
    await db.commit()
    await db.refresh(faq)
    
    return faq


@router.delete("/{faq_id}", response_model=Message)
async def delete_faq(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_staff)
):
    """Delete a FAQ (Admin only)."""
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found"
        )
    
    await db.delete(faq)
    await db.commit()
    
    return {"message": "FAQ deleted successfully"}

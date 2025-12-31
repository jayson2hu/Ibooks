"""
Contact information endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from app.schemas.common import Message
from app.models.contact import Contact


router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("", response_model=List[ContactResponse])
async def list_contacts(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    List all contact information.
    
    - **active_only**: Only return active contacts (default: True)
    """
    query = select(Contact).order_by(Contact.display_order)
    
    if active_only:
        query = query.where(Contact.is_active == True)
    
    result = await db.execute(query)
    contacts = result.scalars().all()
    
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """Get contact by ID."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    return contact


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create a new contact (Admin only)."""
    new_contact = Contact(**contact_data.model_dump())
    
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    
    return new_contact


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update a contact (Admin only)."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Update fields
    update_data = contact_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    await db.commit()
    await db.refresh(contact)
    
    return contact


@router.delete("/{contact_id}", response_model=Message)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Delete a contact (Admin only)."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    await db.delete(contact)
    await db.commit()
    
    return {"message": "Contact deleted successfully"}

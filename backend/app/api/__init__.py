"""
API package router.
"""
from fastapi import APIRouter
from app.api import v1

router = APIRouter()
router.include_router(v1.router)

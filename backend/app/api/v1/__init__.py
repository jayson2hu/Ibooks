"""
API v1 router aggregation.
"""
from fastapi import APIRouter
from app.api.v1 import auth, resources, categories, contacts, search, admin, seo, bulk_import, faqs, settings


router = APIRouter()

# Include all v1 routers
router.include_router(auth.router)
router.include_router(resources.router)
router.include_router(categories.router)
router.include_router(contacts.router)
router.include_router(faqs.router)
router.include_router(search.router)
router.include_router(admin.router)
router.include_router(seo.router)
router.include_router(bulk_import.router)
router.include_router(settings.router)

"""
Bulk import endpoints for admin.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import os
from pathlib import Path
from app.database import get_db
from app.dependencies import get_current_admin
from app.utils.bulk_import import import_resources_from_excel, create_import_template_excel
from app.config import settings


router = APIRouter(prefix="/bulk-import", tags=["Bulk Import"])


@router.post("/resources")
async def bulk_import_resources(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Bulk import resources from Excel/CSV file (Admin only).
    
    Expected columns: title, description, excerpt, category_name, tags, price, 
    cloud_link, access_code, file_size, file_format, resource_type, cover_image_url
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.xlsx', '.xls', '.csv']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel (.xlsx, .xls) or CSV files are supported"
        )
    
    # Save uploaded file temporarily
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    temp_file_path = upload_dir / f"import_{current_user.id}_{file.filename}"
    
    try:
        # Save file
        async with aiofiles.open(temp_file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Import resources
        if file_ext == '.csv':
            from app.utils.bulk_import import import_resources_from_csv
            stats = await import_resources_from_csv(str(temp_file_path), db)
        else:
            stats = await import_resources_from_excel(str(temp_file_path), db)
        
        return {
            "message": "Import completed",
            "statistics": stats
        }
    
    finally:
        # Clean up temporary file
        if temp_file_path.exists():
            os.remove(temp_file_path)


@router.get("/template")
async def download_import_template(
    current_user = Depends(get_current_admin)
):
    """
    Download Excel template for bulk import (Admin only).
    """
    from fastapi.responses import FileResponse
    
    # Create template
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    template_path = upload_dir / "resource_import_template.xlsx"
    create_import_template_excel(str(template_path))
    
    return FileResponse(
        path=str(template_path),
        filename="resource_import_template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

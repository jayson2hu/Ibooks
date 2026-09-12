"""
Bulk import endpoints for admin.
"""
import asyncio

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
from pathlib import Path
from uuid import uuid4
from app.database import get_db
from app.dependencies import get_current_admin
from app.utils.bulk_import import import_resources_from_excel, create_import_template_excel
from app.config import settings


router = APIRouter(prefix="/bulk-import", tags=["Bulk Import"])
UPLOAD_CHUNK_SIZE = 1024 * 1024


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
    temp_file_path: Path | None = None
    try:
        # Only the suffix is retained; the client-provided path never reaches disk.
        file_ext = Path(file.filename or "").suffix.lower()
        if file_ext not in [".xlsx", ".xls", ".csv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only Excel (.xlsx, .xls) or CSV files are supported",
            )

        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = upload_dir / f"import_{uuid4().hex}{file_ext}"

        total_size = 0
        async with aiofiles.open(temp_file_path, 'xb') as f:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > settings.MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=(
                            "Uploaded file exceeds the "
                            f"{settings.MAX_UPLOAD_SIZE}-byte limit"
                        ),
                    )
                await f.write(chunk)
        
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
        try:
            await file.close()
        finally:
            if temp_file_path is not None:
                temp_file_path.unlink(missing_ok=True)


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
    await asyncio.to_thread(create_import_template_excel, str(template_path))
    
    return FileResponse(
        path=str(template_path),
        filename="resource_import_template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

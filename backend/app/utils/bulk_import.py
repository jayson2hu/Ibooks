"""
Bulk import functionality for resources from Excel/CSV files.
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resource import Resource
from app.models.category import Category
from app.utils.seo import generate_slug
from datetime import datetime
from sqlalchemy import select


async def import_resources_from_excel(
    file_path: str,
    db: AsyncSession,
    category_mapping: Dict[str, int] = None
) -> Dict[str, Any]:
    """
    Import resources from Excel file.
    
    Expected columns:
    - title (required)
    - description
    - excerpt
    - category_name
    - tags (comma-separated)
    - price
    - cloud_link
    - access_code
    - file_size
    - file_format
    - resource_type
    - cover_image_url
    
    Args:
        file_path: Path to Excel file
        db: Database session
        category_mapping: Optional mapping of category names to IDs
    
    Returns:
        Dictionary with import statistics
    """
    import pandas as pd

    # Read Excel file
    df = pd.read_excel(file_path)
    return await import_resources_from_dataframe(df, db, category_mapping)


async def import_resources_from_dataframe(
    df: Any,
    db: AsyncSession,
    category_mapping: Dict[str, int] = None
) -> Dict[str, Any]:
    """Import resources from a normalized pandas DataFrame."""
    import pandas as pd
    
    stats = {
        "total": len(df),
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    # Get all categories if mapping not provided
    if category_mapping is None:
        result = await db.execute(select(Category))
        categories = result.scalars().all()
        category_mapping = {cat.name: cat.id for cat in categories}
    
    for idx, row in df.iterrows():
        try:
            # Validate required fields
            if pd.isna(row.get('title')):
                raise ValueError(f"Row {idx + 2}: Missing required field 'title'")
            
            # Generate slug
            slug = generate_slug(row['title'])
            
            # Check if slug exists
            result = await db.execute(select(Resource).where(Resource.slug == slug))
            if result.scalar_one_or_none():
                slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
            
            # Get category ID
            category_id = None
            if not pd.isna(row.get('category_name')):
                category_id = category_mapping.get(row['category_name'])
            
            # Parse tags
            tags = []
            if not pd.isna(row.get('tags')):
                tags = [tag.strip() for tag in str(row['tags']).split(',')]
            
            # Create resource
            resource = Resource(
                title=row['title'],
                slug=slug,
                description=row.get('description') if not pd.isna(row.get('description')) else None,
                excerpt=row.get('excerpt') if not pd.isna(row.get('excerpt')) else None,
                category_id=category_id,
                tags=tags,
                price=float(row.get('price', 0)),
                cloud_link=row.get('cloud_link') if not pd.isna(row.get('cloud_link')) else None,
                access_code=row.get('access_code') if not pd.isna(row.get('access_code')) else None,
                file_size=row.get('file_size') if not pd.isna(row.get('file_size')) else None,
                file_format=row.get('file_format') if not pd.isna(row.get('file_format')) else None,
                resource_type=row.get('resource_type') if not pd.isna(row.get('resource_type')) else None,
                cover_image_url=row.get('cover_image_url') if not pd.isna(row.get('cover_image_url')) else None,
                is_published=True,
                published_at=datetime.utcnow()
            )
            
            db.add(resource)
            stats["success"] += 1
            
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append(f"Row {idx + 2}: {str(e)}")
    
    # Commit all changes
    await db.commit()
    
    return stats


async def import_resources_from_csv(
    file_path: str,
    db: AsyncSession,
    category_mapping: Dict[str, int] = None
) -> Dict[str, Any]:
    """
    Import resources from CSV file.
    
    Same format as Excel import.
    """
    import pandas as pd

    # Read CSV file
    df = pd.read_csv(file_path)
    return await import_resources_from_dataframe(df, db, category_mapping)


def create_import_template_excel(output_path: str):
    """
    Create an Excel template for bulk import.
    
    Args:
        output_path: Path to save the template
    """
    import pandas as pd

    template_data = {
        'title': ['示例电子书标题', '示例课程标题'],
        'description': ['这是一本关于...的电子书', '这是一门关于...的课程'],
        'excerpt': ['简短描述', '简短描述'],
        'category_name': ['电子书', '视频课程'],
        'tags': ['Python,编程', 'Web开发,前端'],
        'price': [99.00, 199.00],
        'cloud_link': ['https://pan.baidu.com/s/xxxxx', 'https://pan.baidu.com/s/yyyyy'],
        'access_code': ['abc123', 'xyz789'],
        'file_size': ['2.5 GB', '5 GB'],
        'file_format': ['PDF, EPUB', 'MP4'],
        'resource_type': ['eBook', 'course'],
        'cover_image_url': ['https://example.com/cover1.jpg', 'https://example.com/cover2.jpg']
    }
    
    df = pd.DataFrame(template_data)
    df.to_excel(output_path, index=False)
    
    return output_path

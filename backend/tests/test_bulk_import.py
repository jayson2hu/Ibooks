"""
Tests for bulk import APIs.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.category import Category
from app.models.resource import Resource
from app.models.user import User, UserRole
from app.utils.security import create_access_token, get_password_hash


async def create_user(email: str, role: UserRole = UserRole.USER) -> tuple[User, str]:
    """Create a user and return it with an auth token."""
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            username=email.split("@")[0],
            role=role,
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )
        return user, token


async def create_category(name: str, slug: str) -> Category:
    """Create a category used by imported resources."""
    async with AsyncSessionLocal() as session:
        category = Category(name=name, slug=slug)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


@pytest.mark.asyncio
async def test_regular_user_cannot_use_bulk_import_endpoints(tmp_path, monkeypatch):
    """Bulk import endpoints are admin-only."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    _, token = await create_user("bulk-user@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        import_response = await client.post(
            "/api/v1/bulk-import/resources",
            files={"file": ("resources.csv", b"title\nBlocked\n", "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        template_response = await client.get(
            "/api/v1/bulk-import/template",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert import_response.status_code == 403
    assert template_response.status_code == 403


@pytest.mark.asyncio
async def test_bulk_import_rejects_unsupported_file_extension(tmp_path, monkeypatch):
    """Bulk import validates uploaded file extension before parsing."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    _, token = await create_user("bulk-invalid-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/bulk-import/resources",
            files={"file": ("resources.txt", b"title\nInvalid\n", "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only Excel (.xlsx, .xls) or CSV files are supported"


@pytest.mark.asyncio
async def test_admin_can_bulk_import_resources_from_csv(tmp_path, monkeypatch):
    """Admins can import resources from CSV and temporary files are cleaned up."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    _, token = await create_user("bulk-admin@example.com", UserRole.ADMIN)
    category = await create_category("Ebooks", "ebooks")
    csv_content = (
        "title,description,excerpt,category_name,tags,price,cloud_link,access_code,"
        "file_size,file_format,resource_type,cover_image_url\n"
        "Imported Book,Long description,Short summary,Ebooks,\"python,ebook\",12.50,"
        "https://pan.example.com/imported,abcd,2 MB,PDF,eBook,https://example.com/cover.png\n"
        ",Missing title,,,tag,0,,,,,,\n"
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/bulk-import/resources",
            files={"file": ("resources.csv", csv_content.encode(), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Import completed"
    assert response.json()["statistics"]["total"] == 2
    assert response.json()["statistics"]["success"] == 1
    assert response.json()["statistics"]["failed"] == 1
    assert "Missing required field 'title'" in response.json()["statistics"]["errors"][0]
    assert list(tmp_path.iterdir()) == []

    async with AsyncSessionLocal() as session:
        resource = (await session.execute(
            select(Resource).where(Resource.title == "Imported Book")
        )).scalar_one()

    assert resource.slug == "imported-book"
    assert resource.category_id == category.id
    assert resource.tags == ["python", "ebook"]
    assert str(resource.price) == "12.50"
    assert resource.cloud_link == "https://pan.example.com/imported"
    assert resource.access_code == "abcd"
    assert resource.is_published is True


@pytest.mark.asyncio
async def test_admin_can_download_bulk_import_template(tmp_path, monkeypatch):
    """Admins can download the generated Excel import template."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    _, token = await create_user("bulk-template-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/bulk-import/template",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "resource_import_template.xlsx" in response.headers["content-disposition"]
    assert response.content
    assert (tmp_path / "resource_import_template.xlsx").exists()

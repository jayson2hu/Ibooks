"""
Tests for bulk import APIs.
"""
import asyncio
from io import BytesIO
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile
from httpx import AsyncClient
from sqlalchemy import select

from app.api.v1.bulk_import import bulk_import_resources
from app.database import AsyncSessionLocal
from app.main import app
from app.models.category import Category
from app.models.resource import Resource
from app.models.user import User, UserRole
from app.utils.bulk_import import import_resources_from_csv, import_resources_from_excel
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
async def test_bulk_import_closes_unsupported_upload(tmp_path, monkeypatch):
    """Rejected direct uploads are closed even before a temporary file is created."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    upload = UploadFile(filename="resources.txt", file=BytesIO(b"not supported"))

    with pytest.raises(HTTPException) as exc_info:
        await bulk_import_resources(
            file=upload,
            db=object(),
            current_user=SimpleNamespace(id=1),
        )

    assert exc_info.value.status_code == 400
    assert upload.file.closed
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_bulk_import_rejects_file_over_size_limit(tmp_path, monkeypatch):
    """Oversized uploads return 413 and leave no partial temporary file."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr("app.api.v1.bulk_import.settings.MAX_UPLOAD_SIZE", 16)
    _, token = await create_user("bulk-oversize-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/bulk-import/resources",
            files={"file": ("resources.csv", b"title\nThis is too large\n", "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 413
    assert response.json()["detail"] == "Uploaded file exceeds the 16-byte limit"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_bulk_import_ignores_client_path_in_filename(tmp_path, monkeypatch):
    """Client paths never influence where the server stores an upload."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    imported_paths: list[Path] = []

    async def fake_import(file_path, db):
        path = Path(file_path)
        assert path.is_file()
        imported_paths.append(path)
        return {"total": 0, "success": 0, "failed": 0, "errors": []}

    monkeypatch.setattr("app.utils.bulk_import.import_resources_from_csv", fake_import)
    upload = UploadFile(
        filename="../../outside.csv",
        file=BytesIO(b"title\nSafe\n"),
    )

    response = await bulk_import_resources(
        file=upload,
        db=object(),
        current_user=SimpleNamespace(id=1),
    )

    assert response["message"] == "Import completed"
    assert len(imported_paths) == 1
    assert imported_paths[0].parent.resolve() == tmp_path.resolve()
    assert imported_paths[0].name.startswith("import_")
    assert "outside" not in imported_paths[0].name
    assert not imported_paths[0].exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_bulk_import_cleans_up_when_parser_fails(tmp_path, monkeypatch):
    """Parser failures close the upload and remove the complete temporary file."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    parsed_paths: list[Path] = []

    async def failing_import(file_path, db):
        path = Path(file_path)
        assert path.read_bytes() == b"title\nBroken\n"
        parsed_paths.append(path)
        raise ValueError("invalid CSV")

    monkeypatch.setattr("app.utils.bulk_import.import_resources_from_csv", failing_import)
    upload = UploadFile(filename="resources.csv", file=BytesIO(b"title\nBroken\n"))

    with pytest.raises(ValueError, match="invalid CSV"):
        await bulk_import_resources(
            file=upload,
            db=object(),
            current_user=SimpleNamespace(id=1),
        )

    assert len(parsed_paths) == 1
    assert upload.file.closed
    assert not parsed_paths[0].exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_bulk_import_cleans_up_when_upload_close_fails(tmp_path, monkeypatch):
    """A close error cannot prevent removal of the temporary upload."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    parsed_paths: list[Path] = []

    async def fake_import(file_path, db):
        parsed_paths.append(Path(file_path))
        return {"total": 0, "success": 0, "failed": 0, "errors": []}

    async def failing_close():
        raise OSError("close failed")

    monkeypatch.setattr("app.utils.bulk_import.import_resources_from_csv", fake_import)
    upload = UploadFile(filename="resources.csv", file=BytesIO(b"title\nSafe\n"))
    monkeypatch.setattr(upload, "close", failing_close)

    with pytest.raises(OSError, match="close failed"):
        await bulk_import_resources(
            file=upload,
            db=object(),
            current_user=SimpleNamespace(id=1),
        )

    assert len(parsed_paths) == 1
    assert not parsed_paths[0].exists()
    assert list(tmp_path.iterdir()) == []
    upload.file.close()


@pytest.mark.asyncio
async def test_admin_can_bulk_import_resources_from_csv(tmp_path, monkeypatch):
    """Admins can import resources from CSV and temporary files are cleaned up."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    _, token = await create_user("bulk-admin@example.com", UserRole.ADMIN)
    category = await create_category("Ebooks", "ebooks")
    csv_content = (
        "title,description,excerpt,category_name,tags,price,coin_price,cloud_link,access_code,"
        "file_size,file_format,resource_type,cover_image_url\n"
        "Imported Book,Long description,Short summary,Ebooks,\"python,ebook\",12.50,25,"
        "https://pan.example.com/imported,abcd,2 MB,PDF,eBook,https://example.com/cover.png\n"
        ",Missing title,,,tag,0,0,,,,,,\n"
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
    assert resource.coin_price == 25
    assert resource.cloud_link == "https://pan.example.com/imported"
    assert resource.access_code == "abcd"
    assert resource.is_published is True


@pytest.mark.asyncio
async def test_bulk_import_assigns_unique_slugs_to_three_identical_titles(
    tmp_path,
    monkeypatch,
):
    """Pending rows in one batch receive deterministic numeric slug suffixes."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    _, token = await create_user("bulk-duplicate-admin@example.com", UserRole.ADMIN)
    csv_content = (
        "title,price,coin_price\n"
        "Repeated Title,0,0\n"
        "Repeated Title,0,0\n"
        "Repeated Title,0,0\n"
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/bulk-import/resources",
            files={"file": ("duplicates.csv", csv_content.encode(), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["statistics"] == {
        "total": 3,
        "success": 3,
        "failed": 0,
        "errors": [],
    }
    assert list(tmp_path.iterdir()) == []

    async with AsyncSessionLocal() as session:
        resources = (
            await session.execute(
                select(Resource)
                .where(Resource.title == "Repeated Title")
                .order_by(Resource.slug)
            )
        ).scalars().all()

    assert [resource.slug for resource in resources] == [
        "repeated-title",
        "repeated-title-2",
        "repeated-title-3",
    ]


@pytest.mark.asyncio
async def test_bulk_import_skips_existing_database_slug_suffixes(tmp_path, monkeypatch):
    """Database conflicts advance through the same stable numeric slug sequence."""
    monkeypatch.setattr("app.api.v1.bulk_import.settings.UPLOAD_DIR", str(tmp_path))
    _, token = await create_user("bulk-existing-slug-admin@example.com", UserRole.ADMIN)

    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Resource(title="Existing Base", slug="collision-title"),
                Resource(title="Existing Suffix", slug="collision-title-2"),
            ]
        )
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/bulk-import/resources",
            files={
                "file": (
                    "collision.csv",
                    b"title,price,coin_price\nCollision Title,0,0\n",
                    "text/csv",
                )
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["statistics"]["success"] == 1
    assert list(tmp_path.iterdir()) == []

    async with AsyncSessionLocal() as session:
        resource = (
            await session.execute(
                select(Resource).where(Resource.title == "Collision Title")
            )
        ).scalar_one()

    assert resource.slug == "collision-title-3"


@pytest.mark.parametrize(
    ("importer", "reader_name"),
    [
        (import_resources_from_csv, "read_csv"),
        (import_resources_from_excel, "read_excel"),
    ],
)
@pytest.mark.asyncio
async def test_bulk_import_parsers_run_outside_the_event_loop(
    importer,
    reader_name,
    monkeypatch,
):
    """Pandas file parsing runs in a worker thread rather than blocking asyncio."""
    import pandas as pd

    event_loop_thread = threading.get_ident()
    parser_threads: list[int] = []
    parser_started = threading.Event()
    event_loop_progressed = threading.Event()
    parsed_dataframe = object()
    category_mapping = {"Ebooks": 1}

    def fake_reader(file_path):
        assert file_path == "resources.input"
        parser_threads.append(threading.get_ident())
        parser_started.set()
        if not event_loop_progressed.wait(timeout=2):
            raise AssertionError("Pandas parser blocked the event loop")
        return parsed_dataframe

    async def fake_import(dataframe, db, mapping):
        assert dataframe is parsed_dataframe
        assert mapping is category_mapping
        return {"total": 0, "success": 0, "failed": 0, "errors": []}

    monkeypatch.setattr(pd, reader_name, fake_reader)
    monkeypatch.setattr(
        "app.utils.bulk_import.import_resources_from_dataframe",
        fake_import,
    )

    async def observe_parser_from_event_loop():
        while not parser_started.is_set():
            await asyncio.sleep(0)
        event_loop_progressed.set()

    result, _ = await asyncio.wait_for(
        asyncio.gather(
            importer("resources.input", object(), category_mapping),
            observe_parser_from_event_loop(),
        ),
        timeout=3,
    )

    assert result["success"] == 0
    assert parser_threads
    assert parser_threads[0] != event_loop_thread


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

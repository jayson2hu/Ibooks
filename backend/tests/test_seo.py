"""
Tests for SEO generation APIs.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
import logging
from xml.etree import ElementTree

import pytest
from httpx import AsyncClient

from app import main as main_module
from app.database import AsyncSessionLocal
from app.main import app
from app.models.category import Category
from app.models.resource import Resource
from app.models.user import User, UserRole
from app.static_generator.html_generator import generate_resource_html, save_resource_html
from app.static_generator import startup as startup_seo
from app.static_generator.rss import _as_utc_aware, save_rss_feed
from app.utils.security import create_access_token, get_password_hash
from app.utils.seo import push_to_baidu


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


async def create_resource(slug: str, *, is_published: bool) -> Resource:
    """Create a resource for static page generation tests."""
    async with AsyncSessionLocal() as session:
        resource = Resource(
            title=f"SEO {slug}",
            slug=slug,
            description="SEO description",
            excerpt="SEO excerpt",
            tags=[],
            price=Decimal("9.90"),
            coin_price=10,
            is_free=False,
            is_published=is_published,
            backup_links=[],
            preview_images=[],
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return resource


class StartupSessionContext:
    """Minimal async session context used to verify startup session lifetimes."""

    def __init__(self, sequence: int) -> None:
        self.session = object()
        self.sequence = sequence
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        return self.session

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        self.exited = True


def install_startup_session_factory(monkeypatch) -> list[StartupSessionContext]:
    """Install a recording factory so each SEO query gets an isolated session."""
    contexts: list[StartupSessionContext] = []

    def create_session() -> StartupSessionContext:
        context = StartupSessionContext(len(contexts))
        contexts.append(context)
        return context

    monkeypatch.setattr(startup_seo, "AsyncSessionLocal", create_session)
    return contexts


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            datetime(2025, 1, 2, 3, 4, 5),
            datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        ),
        (
            datetime(
                2025,
                1,
                2,
                11,
                4,
                5,
                tzinfo=timezone(timedelta(hours=8)),
            ),
            datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        ),
    ],
)
def test_rss_datetime_normalization_supports_naive_and_aware(value, expected):
    """RSS timestamps are always converted to a timezone-aware UTC value."""
    normalized = _as_utc_aware(value)

    assert normalized == expected
    assert normalized.utcoffset() == timedelta(0)


@pytest.mark.asyncio
async def test_save_rss_feed_handles_category_and_naive_datetimes(
    tmp_path,
    monkeypatch,
):
    """A real SQLite query can generate a categorized RSS file from naive UTC."""
    published_at = datetime(2025, 1, 2, 3, 4, 5)
    updated_at = datetime(2025, 1, 3, 4, 5, 6)
    monkeypatch.setattr(
        "app.static_generator.rss.settings.SITE_URL",
        "https://ibooks.test",
    )

    async with AsyncSessionLocal() as session:
        category = Category(
            name="RSS Books",
            slug="rss-books",
            is_active=True,
        )
        session.add(category)
        await session.flush()
        session.add(
            Resource(
                title="Real RSS resource",
                slug="real-rss-resource",
                description="Generated without mocking save_rss_feed",
                category_id=category.id,
                tags=[],
                price=Decimal("1.00"),
                coin_price=1,
                is_free=False,
                is_published=True,
                backup_links=[],
                preview_images=[],
                published_at=published_at,
                updated_at=updated_at,
            )
        )
        await session.commit()

    output_path = tmp_path / "nested" / "rss.xml"
    async with AsyncSessionLocal() as session:
        saved_path = await save_rss_feed(session, output_path)

    assert saved_path == str(output_path)
    root = ElementTree.fromstring(output_path.read_text(encoding="utf-8"))
    item = root.find("./channel/item")
    assert item is not None
    assert item.findtext("title") == "Real RSS resource"
    assert item.findtext("category") == "RSS Books"
    published_text = item.findtext("pubDate")
    assert published_text is not None
    assert parsedate_to_datetime(published_text) == published_at.replace(
        tzinfo=timezone.utc
    )


@pytest.mark.asyncio
async def test_startup_seo_generation_is_skipped_when_disabled(monkeypatch):
    """The disabled flag must avoid database access and filesystem writes."""
    calls: list[str] = []

    def unexpected_session():
        calls.append("session")
        raise AssertionError("SEO startup opened a database session while disabled")

    async def unexpected_async_write(*args, **kwargs):
        calls.append("async-write")
        raise AssertionError("SEO startup wrote a file while disabled")

    def unexpected_sync_write(*args, **kwargs):
        calls.append("sync-write")
        raise AssertionError("SEO startup wrote a file while disabled")

    monkeypatch.setattr(startup_seo.settings, "SEO_AUTO_GENERATE", False)
    monkeypatch.setattr(startup_seo, "AsyncSessionLocal", unexpected_session)
    monkeypatch.setattr(startup_seo, "save_sitemap", unexpected_async_write)
    monkeypatch.setattr(startup_seo, "save_rss_feed", unexpected_async_write)
    monkeypatch.setattr(startup_seo, "save_robots_txt", unexpected_sync_write)

    generated = await startup_seo.generate_startup_seo_files()

    assert generated is False
    assert calls == []


@pytest.mark.asyncio
async def test_startup_seo_generation_creates_all_local_artifacts(monkeypatch):
    """Enabled startup generation refreshes all three files with short sessions."""
    calls: list[tuple[str, object | None]] = []
    contexts = install_startup_session_factory(monkeypatch)

    async def fake_save_sitemap(db):
        calls.append(("sitemap.xml", db))

    async def fake_save_rss_feed(db):
        calls.append(("rss.xml", db))

    def fake_save_robots_txt():
        calls.append(("robots.txt", None))

    monkeypatch.setattr(startup_seo.settings, "SEO_AUTO_GENERATE", True)
    monkeypatch.setattr(startup_seo, "save_sitemap", fake_save_sitemap)
    monkeypatch.setattr(startup_seo, "save_rss_feed", fake_save_rss_feed)
    monkeypatch.setattr(startup_seo, "save_robots_txt", fake_save_robots_txt)

    generated = await startup_seo.generate_startup_seo_files()

    assert generated is True
    assert [artifact for artifact, _ in calls] == [
        "sitemap.xml",
        "rss.xml",
        "robots.txt",
    ]
    assert len(contexts) == 2
    assert calls[0][1] is contexts[0].session
    assert calls[1][1] is contexts[1].session
    assert all(context.entered and context.exited for context in contexts)


@pytest.mark.asyncio
async def test_startup_seo_failure_is_safe_and_does_not_skip_other_files(
    monkeypatch,
    caplog,
):
    """One generator failure is sanitized while the remaining files still run."""
    secret = "database-password=must-not-appear"
    calls: list[str] = []
    contexts = install_startup_session_factory(monkeypatch)

    async def failing_sitemap(db):
        calls.append("sitemap.xml")
        raise RuntimeError(secret)

    async def successful_rss(db):
        calls.append("rss.xml")

    def successful_robots():
        calls.append("robots.txt")

    monkeypatch.setattr(startup_seo.settings, "SEO_AUTO_GENERATE", True)
    monkeypatch.setattr(startup_seo, "save_sitemap", failing_sitemap)
    monkeypatch.setattr(startup_seo, "save_rss_feed", successful_rss)
    monkeypatch.setattr(startup_seo, "save_robots_txt", successful_robots)

    with caplog.at_level(logging.ERROR, logger=startup_seo.__name__):
        generated = await startup_seo.generate_startup_seo_files()

    assert generated is False
    assert calls == ["sitemap.xml", "rss.xml", "robots.txt"]
    assert all(context.entered and context.exited for context in contexts)
    failure_record = next(
        record
        for record in caplog.records
        if getattr(record, "event", None) == "seo_startup_generation_failed"
    )
    assert failure_record.failed_artifacts == ["sitemap.xml"]
    assert failure_record.error_types == ["RuntimeError"]
    assert secret not in caplog.text


@pytest.mark.asyncio
async def test_startup_seo_never_submits_to_external_search_engines(monkeypatch):
    """Startup remains local even when optional submission flags are enabled."""
    contexts = install_startup_session_factory(monkeypatch)
    submission_calls: list[list[str]] = []

    async def fake_save_file(db):
        return None

    def fake_save_robots():
        return None

    async def unexpected_baidu_submission(urls):
        submission_calls.append(urls)
        raise AssertionError("Startup SEO must not submit URLs externally")

    monkeypatch.setattr(startup_seo.settings, "SEO_AUTO_GENERATE", True)
    monkeypatch.setattr(startup_seo.settings, "SEO_SUBMIT_BAIDU", True)
    monkeypatch.setattr(startup_seo.settings, "SEO_SUBMIT_GOOGLE", True)
    monkeypatch.setattr(startup_seo.settings, "SEO_SUBMIT_360", True)
    monkeypatch.setattr(startup_seo.settings, "BAIDU_API_KEY", "configured-secret")
    monkeypatch.setattr(startup_seo, "save_sitemap", fake_save_file)
    monkeypatch.setattr(startup_seo, "save_rss_feed", fake_save_file)
    monkeypatch.setattr(startup_seo, "save_robots_txt", fake_save_robots)
    monkeypatch.setattr(
        "app.api.v1.seo.push_to_baidu",
        unexpected_baidu_submission,
    )

    generated = await startup_seo.generate_startup_seo_files()

    assert generated is True
    assert submission_calls == []
    assert len(contexts) == 2


@pytest.mark.asyncio
async def test_lifespan_continues_when_startup_seo_reports_failure(monkeypatch):
    """Best-effort SEO failure does not prevent the application from yielding."""
    events: list[str] = []

    async def fake_init_db(*, bootstrap_schema):
        events.append(f"database:{bootstrap_schema}")

    async def fake_generate_startup_seo_files():
        events.append("seo-failed")
        return False

    async def fake_close_db():
        events.append("database-closed")

    monkeypatch.setattr(main_module, "setup_logging", lambda: events.append("logging"))
    monkeypatch.setattr(main_module, "init_db", fake_init_db)
    monkeypatch.setattr(
        main_module,
        "generate_startup_seo_files",
        fake_generate_startup_seo_files,
    )
    monkeypatch.setattr(main_module, "close_db", fake_close_db)
    monkeypatch.setattr(main_module.settings, "SCHEMA_BOOTSTRAP_ENABLED", False)
    monkeypatch.setattr(main_module.settings, "CRAWLER_SCHEDULER_ENABLED", False)

    async with main_module.lifespan(app):
        events.append("application-running")

    assert events == [
        "logging",
        "database:False",
        "seo-failed",
        "application-running",
        "database-closed",
    ]


@pytest.mark.asyncio
async def test_regular_user_cannot_generate_seo_files():
    """SEO generation endpoints are admin-only."""
    _, token = await create_user("seo-user@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        sitemap_response = await client.post(
            "/api/v1/seo/generate-sitemap",
            headers={"Authorization": f"Bearer {token}"},
        )
        robots_response = await client.post(
            "/api/v1/seo/generate-robots",
            headers={"Authorization": f"Bearer {token}"},
        )
        static_response = await client.post(
            "/api/v1/seo/generate-static-pages",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert sitemap_response.status_code == 403
    assert robots_response.status_code == 403
    assert static_response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_generate_sitemap_rss_and_wait_for_all_generation(monkeypatch):
    """Generate-all returns only after every artifact has succeeded."""
    _, token = await create_user("seo-admin@example.com", UserRole.ADMIN)
    calls: list[str] = []

    async def fake_save_sitemap(db):
        calls.append("sitemap")

    async def fake_save_rss_feed(db):
        calls.append("rss")

    def fake_save_robots_txt():
        calls.append("robots")

    monkeypatch.setattr("app.api.v1.seo.save_sitemap", fake_save_sitemap)
    monkeypatch.setattr("app.api.v1.seo.save_rss_feed", fake_save_rss_feed)
    monkeypatch.setattr("app.api.v1.seo.save_robots_txt", fake_save_robots_txt)

    async with AsyncClient(app=app, base_url="http://test") as client:
        sitemap_response = await client.post(
            "/api/v1/seo/generate-sitemap",
            headers={"Authorization": f"Bearer {token}"},
        )
        rss_response = await client.post(
            "/api/v1/seo/generate-rss",
            headers={"Authorization": f"Bearer {token}"},
        )
        all_response = await client.post(
            "/api/v1/seo/generate-all",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert sitemap_response.status_code == 200
    assert sitemap_response.json()["message"] == "Sitemap generation started"
    assert rss_response.status_code == 200
    assert rss_response.json()["message"] == "RSS feed generation started"
    assert all_response.status_code == 200
    assert all_response.json() == {
        "message": "SEO 文件生成完成",
        "generated": ["sitemap.xml", "rss.xml", "robots.txt"],
    }
    assert calls == ["sitemap", "rss", "sitemap", "rss", "robots"]


@pytest.mark.asyncio
async def test_admin_generate_all_reports_safe_partial_failure(monkeypatch):
    """All artifacts are attempted and internal exception text is never exposed."""
    _, token = await create_user("seo-failure-admin@example.com", UserRole.ADMIN)
    calls: list[str] = []
    secret = "database-password=must-not-be-returned"

    async def fake_save_sitemap(db):
        calls.append("sitemap.xml")

    async def failing_save_rss_feed(db):
        calls.append("rss.xml")
        raise RuntimeError(secret)

    def fake_save_robots_txt():
        calls.append("robots.txt")

    monkeypatch.setattr("app.api.v1.seo.save_sitemap", fake_save_sitemap)
    monkeypatch.setattr("app.api.v1.seo.save_rss_feed", failing_save_rss_feed)
    monkeypatch.setattr("app.api.v1.seo.save_robots_txt", fake_save_robots_txt)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/seo/generate-all",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "message": "部分 SEO 文件生成失败，请重试",
            "generated": ["sitemap.xml", "robots.txt"],
            "failed": ["rss.xml"],
        }
    }
    assert calls == ["sitemap.xml", "rss.xml", "robots.txt"]
    assert secret not in response.text


@pytest.mark.asyncio
async def test_admin_generate_robots_writes_robots_file(tmp_path, monkeypatch):
    """Admin can generate robots.txt in the configured static directory."""
    monkeypatch.setattr("app.static_generator.robots.settings.STATIC_PAGES_DIR", str(tmp_path))
    monkeypatch.setattr("app.static_generator.robots.settings.SITE_URL", "https://ibooks.test")
    _, token = await create_user("seo-robots-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/seo/generate-robots",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "robots.txt generated successfully"
    robots = (tmp_path / "robots.txt").read_text()
    assert "Sitemap: https://ibooks.test/sitemap.xml" in robots
    assert "Disallow: /api/" in robots


@pytest.mark.asyncio
async def test_admin_generate_static_pages_for_published_resources(monkeypatch):
    """Static page generation exports only published resources."""
    _, token = await create_user("seo-static-admin@example.com", UserRole.ADMIN)
    published = await create_resource("published-static", is_published=True)
    await create_resource("draft-static", is_published=False)
    generated: list[dict] = []

    def fake_save_resource_html(resource_data):
        generated.append(resource_data)

    monkeypatch.setattr("app.api.v1.seo.save_resource_html", fake_save_resource_html)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/seo/generate-static-pages",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Static page generation started"
    assert generated == [
        {
            "title": published.title,
            "slug": "published-static",
            "description": "SEO description",
            "excerpt": "SEO excerpt",
            "meta_title": None,
            "meta_description": None,
            "meta_keywords": None,
            "cover_image_url": None,
            "price": 9.9,
        }
    ]


@pytest.mark.asyncio
async def test_baidu_submission_skips_when_disabled(monkeypatch):
    """Disabled URL submission must not make an external request."""
    monkeypatch.setattr("app.utils.seo.settings.SEO_SUBMIT_BAIDU", False)
    monkeypatch.setattr("app.utils.seo.settings.BAIDU_API_KEY", "")

    result = await push_to_baidu(["https://ibooks.test/resources/example"])

    assert result == {"skipped": True, "submitted": 0}


@pytest.mark.asyncio
async def test_baidu_submission_deduplicates_urls(monkeypatch):
    """Enabled submission sends each normalized URL once."""
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"success": 1, "remain": 99}

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            captured.update({"url": url, **kwargs})
            return FakeResponse()

    monkeypatch.setattr("app.utils.seo.settings.SEO_SUBMIT_BAIDU", True)
    monkeypatch.setattr("app.utils.seo.settings.BAIDU_API_KEY", "secret")
    monkeypatch.setattr("app.utils.seo.settings.SITE_URL", "https://ibooks.test")
    monkeypatch.setattr("app.utils.seo.httpx.AsyncClient", FakeClient)

    result = await push_to_baidu([
        "https://ibooks.test/resources/example",
        "https://ibooks.test/resources/example",
    ])

    assert result == {"success": 1, "remain": 99, "submitted": 1}
    assert captured["url"] == "https://data.zz.baidu.com/urls"
    assert captured["params"] == {"site": "https://ibooks.test", "token": "secret"}
    assert captured["content"] == "https://ibooks.test/resources/example"


@pytest.mark.asyncio
async def test_generated_sitemap_submits_public_urls(tmp_path, monkeypatch):
    """Sitemap generation forwards all loc entries when Baidu is enabled."""
    sitemap_path = tmp_path / "sitemap.xml"
    sitemap_path.write_text(
        '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        '<url><loc>https://ibooks.test/</loc></url>'
        '<url><loc>https://ibooks.test/resources/example</loc></url>'
        '</urlset>',
        encoding="utf-8",
    )
    submitted = []

    async def fake_save_sitemap(db):
        return str(sitemap_path)

    async def fake_push_to_baidu(urls):
        submitted.extend(urls)
        return {"submitted": len(urls)}

    monkeypatch.setattr("app.api.v1.seo.settings.SEO_SUBMIT_BAIDU", True)
    monkeypatch.setattr("app.api.v1.seo.settings.BAIDU_API_KEY", "secret")
    monkeypatch.setattr("app.api.v1.seo.save_sitemap", fake_save_sitemap)
    monkeypatch.setattr("app.api.v1.seo.push_to_baidu", fake_push_to_baidu)

    from app.api.v1.seo import _generate_sitemap_and_submit

    await _generate_sitemap_and_submit(None)

    assert submitted == [
        "https://ibooks.test/",
        "https://ibooks.test/resources/example",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "content", "media_type"),
    [
        ("sitemap.xml", "<urlset></urlset>", "application/xml"),
        ("rss.xml", "<rss></rss>", "application/xml"),
        ("robots.txt", "User-agent: *", "text/plain"),
    ],
)
async def test_public_seo_files_use_configured_static_directory(
    tmp_path,
    monkeypatch,
    filename,
    content,
    media_type,
):
    """Public SEO routes serve the files written to STATIC_PAGES_DIR."""
    monkeypatch.setattr("app.main.settings.STATIC_PAGES_DIR", str(tmp_path))
    (tmp_path / filename).write_text(content, encoding="utf-8")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/{filename}")

    assert response.status_code == 200
    assert response.text == content
    assert response.headers["content-type"].startswith(media_type)


@pytest.mark.asyncio
async def test_missing_public_seo_file_returns_not_found(tmp_path, monkeypatch):
    """A missing generated file must not look like a successful SEO response."""
    monkeypatch.setattr("app.main.settings.STATIC_PAGES_DIR", str(tmp_path))

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/sitemap.xml")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sitemap not found. Please generate it first."


@pytest.mark.asyncio
async def test_public_generated_resource_page_is_served_as_html(tmp_path, monkeypatch):
    """The generator output is publicly readable by its valid resource slug."""
    monkeypatch.setattr("app.main.settings.STATIC_PAGES_DIR", str(tmp_path))
    monkeypatch.setattr("app.main.settings.SITE_URL", "https://ibooks.test")
    save_resource_html(
        {
            "title": "Static resource",
            "slug": "safe-resource-2",
            "description": "静态资源页",
            "price": 9.9,
        }
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/generated/resources/safe-resource-2.html")

    assert response.status_code == 200
    assert "<h1>Static resource</h1>" in response.text
    assert 'href="https://ibooks.test/resources/safe-resource-2"' in response.text
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "content-disposition" not in response.headers


@pytest.mark.asyncio
async def test_missing_generated_resource_page_returns_not_found(tmp_path, monkeypatch):
    """A valid slug without a generated artifact returns a real 404."""
    monkeypatch.setattr("app.main.settings.STATIC_PAGES_DIR", str(tmp_path))

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/generated/resources/not-generated.html")

    assert response.status_code == 404
    assert response.json()["detail"] == "Generated resource page not found"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_path",
    [
        "/generated/resources/UPPERCASE.html",
        "/generated/resources/unsafe_slug.html",
        "/generated/resources/...html",
        "/generated/resources/%2e%2e%2foutside.html",
        f"/generated/resources/{'a' * 201}.html",
    ],
)
async def test_generated_resource_page_rejects_unsafe_slugs(
    tmp_path,
    monkeypatch,
    request_path,
):
    """Invalid slugs and traversal attempts cannot select files on disk."""
    monkeypatch.setattr("app.main.settings.STATIC_PAGES_DIR", str(tmp_path))
    (tmp_path / "outside.html").write_text("must not be served", encoding="utf-8")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(request_path)

    assert response.status_code == 404
    assert "must not be served" not in response.text


def test_static_generator_rejects_unsafe_resource_slug(tmp_path, monkeypatch):
    """Generation cannot write a resource slug outside the configured directory."""
    monkeypatch.setattr(
        "app.static_generator.html_generator.settings.STATIC_PAGES_DIR",
        str(tmp_path),
    )

    with pytest.raises(ValueError, match="Invalid resource slug"):
        save_resource_html({"title": "Unsafe", "slug": "../outside"})

    assert list(tmp_path.rglob("*.html")) == []


def test_generated_resource_html_escapes_untrusted_content(monkeypatch):
    """Public generated pages encode resource text and JSON-LD safely."""
    monkeypatch.setattr(
        "app.static_generator.html_generator.settings.SITE_URL",
        "https://ibooks.test",
    )
    payload = '</script><script>alert("stored-xss")</script>'

    html = generate_resource_html(
        {
            "title": "Safe title",
            "slug": "safe-title",
            "description": payload,
            "excerpt": payload,
        }
    )

    assert payload not in html
    assert "&lt;/script&gt;&lt;script&gt;alert" in html
    assert "\\u003c/script\\u003e\\u003cscript\\u003ealert" in html

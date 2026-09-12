"""
Tests for the 1024 crawler parsing and sync logic.
"""

from datetime import datetime

import pytest
from sqlalchemy import event, select

from app.database import engine
from app.models.resource import Resource
from app.models.site_settings import SiteSetting

from app.services.crawler_service import (
    Source1024SyncService,
    source_1024_crawler_manager,
)
from app.services.crawlers.source_1024 import (
    ExternalResourceCandidate,
    Source1024Crawler,
)


SAMPLE_LISTING_HTML = """
<article id="post-22083" class="post post-grid post-22083 type-post status-publish format-standard has-post-thumbnail hentry category-hige">
  <div class="entry-media">
    <div class="placeholder">
      <a href="https://www.1024zyz.com/22083.html" title="尹成Golang全栈VIP实战课">
        <img class="lazyload" data-src="https://www.1024zyz.com/wp-content/uploads/2026/03/example.png" alt="尹成Golang全栈VIP实战课" />
      </a>
    </div>
  </div>
  <div class="entry-wrapper">
    <span class="meta-category-dot"><a href="https://www.1024zyz.com/hige" rel="category">高薪课程</a></span>
    <header class="entry-header">
      <h2 class="entry-title"><a href="https://www.1024zyz.com/22083.html" rel="bookmark">尹成Golang全栈VIP实战课</a></h2>
    </header>
    <div class="entry-excerpt">【资源目录】：Golang 课程精华内容</div>
    <div class="entry-footer">
      <div class="entry-meta">
        <span class="meta-date">
          <time datetime="2026-03-19T07:06:42+08:00">2026-03-19</time>
        </span>
      </div>
    </div>
  </div>
</article>
"""

CURRENT_LISTING_HTML = """
<article class="post-item item-grid">
  <div class="entry-media ratio ratio-3x2">
    <a class="media-img lazy bg-cover bg-center"
       href="https://www.1024zyz.com/22559.html"
       data-bg="https://www.1024zyz.com/wp-content/uploads/2026/09/current.png?v=1">
    </a>
  </div>
  <div class="entry-wrapper">
    <div class="entry-cat-dot"><a href="https://www.1024zyz.com/hige">高薪课程</a></div>
    <h2 class="entry-title extra-class">
      <a href="https://www.1024zyz.com/22559.html">智能运维课程</a>
    </h2>
    <div class="entry-desc">【资源目录】：课程更新内容</div>
    <div class="entry-meta">
      <time class="pub-date" datetime="2026-09-07T07:08:44+08:00">3天前</time>
    </div>
  </div>
</article>
"""


def test_parse_1024_listing_page():
    """The crawler should extract public metadata from listing HTML."""
    candidates = Source1024Crawler.parse_listing_page(SAMPLE_LISTING_HTML)

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.external_id == "22083"
    assert candidate.title == "尹成Golang全栈VIP实战课"
    assert candidate.source_url == "https://www.1024zyz.com/22083.html"
    assert (
        candidate.cover_image_url
        == "https://www.1024zyz.com/wp-content/uploads/2026/03/example.png"
    )
    assert candidate.resource_type == "高薪课程"
    assert candidate.external_published_at == datetime(2026, 3, 19, 7, 6, 42)
    assert "external source" in candidate.tags


def test_parse_current_1024_listing_markup_without_post_id_attribute():
    """The parser should support the site's current article/card markup."""
    candidates = Source1024Crawler.parse_listing_page(CURRENT_LISTING_HTML)

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.external_id == "22559"
    assert candidate.title == "智能运维课程"
    assert candidate.excerpt == "【资源目录】：课程更新内容"
    assert candidate.resource_type == "高薪课程"
    assert candidate.cover_image_url == (
        "https://www.1024zyz.com/wp-content/uploads/2026/09/current.png?v=1"
    )
    assert candidate.external_published_at == datetime(2026, 9, 7, 7, 8, 44)


@pytest.mark.asyncio
async def test_sync_1024_resources_upserts_records(db_session, monkeypatch):
    """The sync service should create resources first and then update them on subsequent runs."""
    candidate = ExternalResourceCandidate(
        external_id="22083",
        title="尹成Golang全栈VIP实战课",
        source_url="https://www.1024zyz.com/22083.html",
        excerpt="第一版摘要",
        cover_image_url="https://www.1024zyz.com/wp-content/uploads/2026/03/example.png",
        resource_type="高薪课程",
        external_published_at=datetime(2026, 3, 19, 7, 6, 42),
        tags=["高薪课程", "1024 resources", "external source"],
    )

    async def fake_crawl(self, *, max_pages: int):
        return [candidate]

    monkeypatch.setattr(Source1024Crawler, "crawl", fake_crawl)

    service = Source1024SyncService(db_session)
    first_result = await service.sync(
        max_pages=1, timeout_seconds=5, target_category_id=None
    )
    await db_session.commit()

    assert first_result.imported_count == 1
    assert first_result.updated_count == 0

    imported_resource = (await db_session.execute(select(Resource))).scalar_one()
    assert imported_resource.is_published is False
    assert imported_resource.published_at is None

    candidate.excerpt = "更新后的摘要"
    second_result = await service.sync(
        max_pages=1, timeout_seconds=5, target_category_id=None
    )

    assert second_result.imported_count == 0
    assert second_result.updated_count == 1


@pytest.mark.asyncio
async def test_sync_batches_resource_lookups_for_multiple_candidates(
    db_session,
    monkeypatch,
):
    """Sync query volume should stay constant as a crawl page grows."""
    candidates = [
        ExternalResourceCandidate(
            external_id=str(23000 + index),
            title=f"批量资源 {index}",
            source_url=f"https://www.1024zyz.com/{23000 + index}.html",
        )
        for index in range(5)
    ]

    async def fake_crawl(self, *, max_pages: int):
        return candidates

    monkeypatch.setattr(Source1024Crawler, "crawl", fake_crawl)
    resource_selects: list[str] = []

    def record_resource_select(
        connection,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ):
        normalized = statement.upper()
        if normalized.lstrip().startswith("SELECT") and "FROM RESOURCES" in normalized:
            resource_selects.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record_resource_select)
    try:
        result = await Source1024SyncService(db_session).sync(
            max_pages=1,
            timeout_seconds=5,
            target_category_id=None,
        )
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", record_resource_select)

    assert result.imported_count == len(candidates)
    assert len(resource_selects) == 2


@pytest.mark.asyncio
async def test_sync_deduplicates_repeated_candidates_without_per_row_flush(
    db_session,
    monkeypatch,
):
    """Repeated crawl candidates should still produce a single resource row."""
    candidate = ExternalResourceCandidate(
        external_id="23099",
        title="重复候选资源",
        source_url="https://www.1024zyz.com/23099.html",
    )

    async def fake_crawl(self, *, max_pages: int):
        return [candidate, candidate]

    monkeypatch.setattr(Source1024Crawler, "crawl", fake_crawl)
    result = await Source1024SyncService(db_session).sync(
        max_pages=1,
        timeout_seconds=5,
        target_category_id=None,
    )

    resources = (await db_session.execute(select(Resource))).scalars().all()
    assert result.imported_count == 1
    assert result.skipped_count == 1
    assert len(resources) == 1


@pytest.mark.asyncio
async def test_sync_1024_resources_respects_enabled_optional_fields(
    db_session, monkeypatch
):
    """Optional fields disabled in crawler settings should not be written into imported resources."""
    candidate = ExternalResourceCandidate(
        external_id="22084",
        title="只同步必选字段",
        source_url="https://www.1024zyz.com/22084.html",
        excerpt="这段摘要不应被同步",
        cover_image_url="https://www.1024zyz.com/wp-content/uploads/2026/03/disabled.png",
        resource_type="高薪课程",
        external_published_at=datetime(2026, 3, 20, 9, 0, 0),
        tags=["高薪课程", "1024 resources", "external source"],
    )

    async def fake_crawl(self, *, max_pages: int):
        return [candidate]

    monkeypatch.setattr(Source1024Crawler, "crawl", fake_crawl)

    service = Source1024SyncService(db_session, enabled_fields=[])
    result = await service.sync(max_pages=1, timeout_seconds=5, target_category_id=None)
    await db_session.commit()

    assert result.imported_count == 1

    resource = (await db_session.execute(select(Resource))).scalar_one()
    assert resource.title == "只同步必选字段"
    assert resource.description == "只同步必选字段"
    assert resource.excerpt is None
    assert resource.cover_image_url is None
    assert resource.resource_type is None
    assert resource.tags == []


@pytest.mark.asyncio
async def test_sync_does_not_republish_manually_unpublished_resource(
    db_session, monkeypatch
):
    """A crawler sync must preserve an administrator's unpublished state."""
    candidate = ExternalResourceCandidate(
        external_id="22085",
        title="人工下架后保持草稿",
        source_url="https://www.1024zyz.com/22085.html",
        excerpt="同步不应覆盖发布状态",
        external_published_at=datetime(2026, 3, 21, 10, 0, 0),
    )

    async def fake_crawl(self, *, max_pages: int):
        return [candidate]

    monkeypatch.setattr(Source1024Crawler, "crawl", fake_crawl)

    service = Source1024SyncService(db_session)
    await service.sync(max_pages=1, timeout_seconds=5, target_category_id=None)
    await db_session.commit()

    resource = (await db_session.execute(select(Resource))).scalar_one()
    resource.is_published = True
    resource.published_at = datetime(2026, 3, 22, 10, 0, 0)
    await db_session.commit()

    resource.is_published = False
    await db_session.commit()

    await service.sync(max_pages=1, timeout_seconds=5, target_category_id=None)
    await db_session.commit()
    await db_session.refresh(resource)

    assert resource.is_published is False


@pytest.mark.asyncio
async def test_crawler_status_returns_available_fields(db_session):
    """Crawler status should expose selectable field metadata for admin UI."""
    db_session.add_all(
        [
            SiteSetting(key="crawler_1024_enabled", value="true", category="crawler"),
            SiteSetting(
                key="crawler_1024_interval_minutes", value="180", category="crawler"
            ),
            SiteSetting(key="crawler_1024_max_pages", value="2", category="crawler"),
            SiteSetting(
                key="crawler_1024_request_timeout_seconds",
                value="15",
                category="crawler",
            ),
            SiteSetting(
                key="crawler_1024_target_category_id", value="", category="crawler"
            ),
            SiteSetting(
                key="crawler_1024_enabled_fields",
                value="excerpt,tags",
                category="crawler",
            ),
            SiteSetting(key="crawler_1024_last_run_at", value="", category="crawler"),
            SiteSetting(
                key="crawler_1024_last_status", value="idle", category="crawler"
            ),
            SiteSetting(key="crawler_1024_last_message", value="", category="crawler"),
            SiteSetting(key="crawler_1024_last_count", value="0", category="crawler"),
        ]
    )
    await db_session.commit()

    status = await source_1024_crawler_manager.get_status(db_session)

    enabled_map = {
        field["key"]: field["enabled"] for field in status["available_fields"]
    }
    required_map = {
        field["key"]: field["required"] for field in status["available_fields"]
    }

    assert enabled_map["title"] is True
    assert enabled_map["source_url"] is True
    assert enabled_map["external_id"] is True
    assert enabled_map["excerpt"] is True
    assert enabled_map["tags"] is True
    assert enabled_map["cover_image_url"] is False
    assert required_map["title"] is True
    assert required_map["excerpt"] is False

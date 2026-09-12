"""Crawler resource identity schema and migration tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import create_engine

from app.models.resource import Resource


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "a3b4c5d6e7f8_add_unique_crawler_resource_identity.py"
)


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "crawler_identity_migration",
        MIGRATION_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_minimal_resources_table(connection) -> None:
    connection.exec_driver_sql(
        """
        CREATE TABLE resources (
            id INTEGER PRIMARY KEY,
            source_site VARCHAR(100),
            source_external_id VARCHAR(255),
            source_url TEXT
        )
        """
    )


def test_resource_model_declares_partial_unique_source_indexes():
    indexes = {index.name: index for index in Resource.__table__.indexes}

    external_identity = indexes["uq_resources_source_site_external_id"]
    assert external_identity.unique is True
    assert [column.name for column in external_identity.columns] == [
        "source_site",
        "source_external_id",
    ]
    assert "source_site IS NOT NULL" in str(
        external_identity.dialect_options["sqlite"]["where"]
    )

    source_url = indexes["uq_resources_source_url"]
    assert source_url.unique is True
    assert [column.name for column in source_url.columns] == ["source_url"]
    assert str(source_url.dialect_options["sqlite"]["where"]) == (
        "source_url IS NOT NULL"
    )


def test_migration_allows_repeated_null_source_identities():
    migration = load_migration()
    engine = create_engine("sqlite+pysqlite:///:memory:")

    with engine.begin() as connection:
        create_minimal_resources_table(connection)
        connection.exec_driver_sql(
            """
            INSERT INTO resources (id, source_site, source_external_id, source_url)
            VALUES (1, NULL, NULL, NULL), (2, NULL, NULL, NULL)
            """
        )
        migration._assert_no_duplicate_sources(connection)


def test_migration_aborts_without_deleting_duplicate_source_rows():
    migration = load_migration()
    engine = create_engine("sqlite+pysqlite:///:memory:")

    with engine.begin() as connection:
        create_minimal_resources_table(connection)
        connection.exec_driver_sql(
            """
            INSERT INTO resources (id, source_site, source_external_id, source_url)
            VALUES
                (1, '1024zyz.com', '22083', 'https://source.invalid/22083'),
                (2, '1024zyz.com', '22083', 'https://source.invalid/22083')
            """
        )

        with pytest.raises(
            RuntimeError,
            match=(
                r"1 duplicate \(source_site, source_external_id\) group\(s\) "
                r"and 1 duplicate source_url group\(s\)"
            ),
        ):
            migration._assert_no_duplicate_sources(connection)

        remaining_rows = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM resources"
        ).scalar_one()
        assert remaining_rows == 2

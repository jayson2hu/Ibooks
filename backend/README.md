# Digital Resource Marketplace - Backend

FastAPI 0.136.3 backend for the Digital Resource Marketplace. Resource purchases
use site coins; Alipay is a coin-recharge channel rather than a direct resource
payment path.

## Features

- 🔐 JWT Authentication
- 📦 Resource Management (CRUD)
- 🏷️ Category Management (Hierarchical)
- 📞 Contact Information Management
- 🔍 Full-text Search
- 📊 Admin Dashboard API
- 📝 Audit Logging
- ⚡ Performance Monitoring
- 🔄 Prometheus Metrics
- 📖 Auto-generated API Docs
- 💰 Wallet, immutable coin ledger, recharge orders, and coin purchases
- 🕷️ Role-scoped crawler management with cross-process leases and source deduplication
- 🔎 Startup and staff-triggered SEO artifact generation

## Quick Start

### 1. Create Environment File

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 2. Install Dependencies

```bash
# requirements-dev.txt includes requirements.txt plus tests, Ruff, and pip-audit.
python -m pip install -r requirements-dev.txt
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs (`DEBUG=true` only)
- ReDoc: http://localhost:8000/api/redoc (`DEBUG=true` only)
- Prometheus Metrics: http://localhost:8000/metrics

### User-list contract

`GET /api/v1/admin/users?page=1&page_size=20` returns the project's standard
paginated object: `items`, `total`, `page`, `page_size`, and `pages`. This is the
current and only `/admin/users` list contract; clients should read users from
`items` rather than expect a top-level array.

### Resource-delivery contract

`GET /api/v1/resources/{slug}/access` is a side-effect-free permission check. A
successful response contains only `has_access`; it never returns a cloud link
and never increments `download_count`. The caller must explicitly use
`POST /api/v1/resources/{slug}/download` to receive `cloud_link`,
`backup_links`, and `access_code`. That endpoint atomically records one
download after applying the same free-resource or paid-order policy.

### Public settings and SEO generation contracts

Anonymous settings endpoints return only allowlisted presentation keys, and
each `PublicSiteSettingResponse` contains only `key` and `value`. Category,
description, update time, and updater identity remain administrative metadata.

`POST /api/v1/seo/generate-all` waits until sitemap, RSS, and robots generation
has finished. A successful response lists the generated files. If only part of
the operation succeeds, the endpoint returns HTTP 500 with safe `generated`
and `failed` filename lists, while internal exception details remain in logs.

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── dependencies.py      # Shared dependencies
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/v1/              # API endpoints
│   ├── middleware/          # Custom middleware
│   ├── utils/               # Utility functions
│   └── static_generator/    # SEO generation
├── requirements.txt          # Production runtime dependencies
├── requirements-dev.txt      # Local tests, lint, and dependency audit
├── Dockerfile
└── .env.example
```

## Environment Variables

See `.env.example` for all available configuration options. Local development
requires `DATABASE_URL`, `REDIS_URL`, and `JWT_SECRET_KEY`; run Alembic before
starting the API.

`SEO_AUTO_GENERATE=true` refreshes only local `sitemap.xml`, `rss.xml`, and
`robots.txt` files during startup. It does not submit URLs externally and a
generation failure does not block API startup. `BAIDU_API_KEY` may stay empty
unless `SEO_SUBMIT_BAIDU=true` is explicitly enabled for Baidu submission.

## Docker

```bash
# From the repository root; Compose applies migrations before Uvicorn starts.
docker compose config --quiet
docker compose up -d --build backend
docker compose logs -f backend
```

## Testing

```bash
python -m pytest tests --cov=app --cov-report=term-missing
ruff check app tests
python -m pip check
python -m pip_audit -r requirements.txt
alembic check
```

Current recorded baseline: `292 passed` with `72.42%` total coverage
(approximately `72%`). Ruff, `pip check`, and `pip-audit` pass, with no known
dependency vulnerabilities. A fresh database also completes
`upgrade -> downgrade -1 -> upgrade`, followed by a clean `alembic check`.

## Remaining Release Validation

- Run the complete production-style Compose and Grafana/Prometheus/Loki stack;
  Docker Hub image-pull timeouts currently require deployment-host network or
  trusted-mirror remediation when they block startup.
- Complete real Alipay sandbox recharge/callback, SMTP delivery, and Baidu URL
  submission using valid credentials and publicly reachable endpoints.
- Confirm product scope before implementing Google Search Console or 360 URL
  submission; only configuration placeholders exist today.

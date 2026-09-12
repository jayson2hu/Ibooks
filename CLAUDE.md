# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iBooks is a Chinese-language digital resource marketplace for e-books, video courses, documents, and similar downloadable/cloud-drive resources.

- Backend: Python 3.11+, FastAPI 0.136.3, SQLAlchemy 2 async ORM, Pydantic v2, PostgreSQL, Redis
- Frontend: Next.js 15.5.25 App Router, React 18, TypeScript, Tailwind CSS 3.4
- Infra: Docker Compose for PostgreSQL, Redis, backend, frontend, Prometheus, Grafana, Loki, and Promtail
- Product status: the core MVP is implemented and is in release-verification/operations closeout. Authentication, role-aware administration, resources, wallet/ledger, coin purchases, recharge orders, paid-resource delivery, email verification/reset, SEO generation, and crawler management have real backend and frontend integrations.
- Do not call the deployment fully production-ready until the full Compose/monitoring runtime and credential-backed external integration checks are complete. Backend/frontend quality gates and desktop/375px public-route browser acceptance are complete. Use `DEV_PLAN.md` for current status; `PROJECT_TODO.md` is explicitly a 2026-04-27 historical audit snapshot.

## Common Commands

### Backend

```bash
cd backend

# Install runtime plus local test/lint/audit dependencies
python -m pip install -r requirements-dev.txt

# Apply schema and run the development server
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000

# Tests and lint
python -m pytest tests -q
python -m pytest tests/test_auth.py -q
python -m pytest tests --cov=app --cov-report=term-missing
ruff check app tests
python -m pip check
python -m pip_audit -r requirements.txt

# Alembic migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
alembic check
```

Backend local development requires `.env` values for at least `DATABASE_URL`, `REDIS_URL`, and `JWT_SECRET_KEY`. The async PostgreSQL URL must use the `postgresql+asyncpg://` driver. Production and Docker startup must use Alembic with `SCHEMA_BOOTSTRAP_ENABLED=false`; schema bootstrap is only an explicit disposable local/test fallback.

By default, tests use a temporary file-backed SQLite database (`sqlite+aiosqlite`) and reset the schema around every test through the application's own engine/session factory. Set a distinct `DATABASE_URL` before importing the app when a test run needs an isolated database file.

### Frontend

```bash
cd frontend

npm install
npm run dev -- --hostname 127.0.0.1
npm test -- --watch=false
npx tsc --noEmit --incremental false
npm run lint -- --no-cache
npm run build
# Run only after a successful production build
npm run start -- --hostname 127.0.0.1
```

Frontend environment variables:

- `NEXT_PUBLIC_API_URL`, default `http://localhost:8000`
- `NEXT_PUBLIC_SITE_URL`, default `http://localhost:3000`

`NEXT_PUBLIC_API_URL` is bundled into browser code. In Docker or production, do not set it to an internal-only host such as `http://backend:8000` unless the browser can resolve that host. Use a public/reverse-proxied API URL for browser access.

### Docker

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs -f backend
docker compose down
```

Expected local ports from `docker-compose.yml`:

- Frontend: `http://127.0.0.1:3000`
- Backend API: `http://127.0.0.1:8000`
- API docs when `DEBUG=true`: `http://localhost:8000/api/docs`
- Prometheus: `http://127.0.0.1:9090` by default
- Grafana: `http://127.0.0.1:3001` by default
- PostgreSQL, Redis, exporters, Loki, and Promtail stay on the private Compose network unless the Compose file is deliberately changed

Compose requires the fail-fast variables documented in `.env.example`, including database/JWT/Grafana secrets, public site/API URLs, CORS origins, and an explicit `ALIPAY_SANDBOX` value. The backend container runs `alembic upgrade head` before Uvicorn starts.

All published ports default to loopback and can be adjusted with `FRONTEND_*`, `BACKEND_*`, and `MONITORING_*` binding variables. Prometheus/Loki retention and Docker log rotation are controlled by `PROMETHEUS_RETENTION`, `LOKI_RETENTION`, `LOG_MAX_SIZE`, and `LOG_MAX_FILES`. Backend file logs, generated SEO files, and uploads use named volumes; use `docker compose logs -f backend` instead of assuming a host `logs/backend` bind mount. Loki TSDB v13 writes to the new `loki_tsdb_data` volume; the legacy `loki_data` volume is deliberately left untouched for backup/export and later manual cleanup.

## Architecture

### Backend

Entry point: `backend/app/main.py`.

Startup flow:

1. `setup_logging()`
2. `init_db(bootstrap_schema=settings.SCHEMA_BOOTSTRAP_ENABLED)`; this performs no schema mutation by default
3. `SEO_AUTO_GENERATE=true` refreshes local sitemap, RSS, and robots artifacts with isolated short sessions; failures are logged without blocking startup and this path never submits URLs externally
4. The optional crawler scheduler starts when `CRAWLER_SCHEDULER_ENABLED=true`
5. CORS and security headers are installed; performance and audit middleware are controlled by settings
6. API routers are mounted under `settings.API_V1_PREFIX`, currently `/api/v1`

Request flow:

HTTP request -> CORS -> optional `PerformanceMiddleware` -> optional `AuditMiddleware` -> router -> FastAPI dependencies -> endpoint handler -> async SQLAlchemy session commit/rollback.

Important backend modules:

- `app/api/v1/`: route modules for auth, resources, categories, contacts, FAQs, search, admin, SEO, bulk import, settings, orders, wallet, signin, recharge, and crawler management
- `app/api/v1/__init__.py`: central router aggregation. Add new v1 routers here
- `app/models/`: SQLAlchemy ORM models; all inherit from `app.database.Base`
- `app/schemas/`: Pydantic request/response schemas
- `app/dependencies.py`: shared DB and auth dependencies, including current-user, admin-only, and admin-or-moderator (`get_current_staff`) checks
- `app/middleware/`: CORS, request audit logging, and performance tracking
- `app/utils/`: security, logging, metrics, SEO helpers, and bulk import utilities
- `app/static_generator/`: sitemap, RSS, robots, and static HTML generation helpers

Database behavior:

- `get_db()` yields an async session, commits after successful request handling, rolls back on exceptions, and closes the session
- The repository contains Alembic revisions for the initial schema, orders, wallets/ledger, coin pricing, signin, recharge, crawler metadata, and the paid-order uniqueness constraint
- The order uniqueness migration enforces at most one paid order per user/resource while still allowing cancelled or pending purchase attempts. The current migration head is `b4c5d6e7f8a9`, adding user session revocation and email-verification expiry
- Production startup relies on `alembic upgrade head`. `Base.metadata.create_all()` and compatibility updates run only when schema bootstrap is explicitly enabled for a disposable local/test database
- The migration chain has recorded empty-database upgrade/downgrade/upgrade validation, including the paid-order partial unique index; repeat that validation whenever constraints or enum-backed columns change

Testing behavior:

- The full backend quality gate recorded on 2026-09-10 is 292 passed with 72.42% coverage; Ruff, `pip check`, and dependency auditing passed then. Ruff and `pip check` were rerun successfully on 2026-09-12; the full backend suite and vulnerability audit were not rerun for that progress-and-push task
- Tests use a temporary file-backed SQLite database and create/drop all tables around each test through the same application engine
- SQLite coverage does not replace PostgreSQL validation for partial indexes, row locking, enum behavior, or migration DDL. Add focused tests and migration checks for schema, authentication, permissions, wallet/order transactions, and external callbacks

### Frontend

The frontend uses Next.js App Router directly under `frontend/src/app`. There are no route-group directories such as `(public)` in the current tree.

Important frontend modules:

- `src/app/`: public pages, resource pages, and admin pages
- `src/app/admin/`: admin dashboard and management pages
- `src/components/admin/`: admin UI components
- `src/components/home/`, `src/components/resource/`, `src/components/layout/`, `src/components/common/`: public-facing UI components
- `src/lib/api.ts`: single Axios client and API wrapper. New frontend API calls should go through this client unless there is a clear reason not to
- `src/hooks/useAuth.ts` and `src/hooks/useAdminAuth.ts`: client-side auth hooks based on `localStorage` token
- `src/types/index.ts`: shared TypeScript types
- `__tests__/`: Jest/Testing Library coverage for core components, API behavior, authentication/role guards, search, the admin dashboard, and audit formatting

Authentication:

- Login stores separate access and refresh JWTs in `localStorage`; refresh tokens rotate on use
- Axios attaches the token as `Authorization: Bearer ...`
- A 401 clears credentials only when they still match the rejected request. If another tab has replaced the stored access token, the client retries once with that token instead of clearing the newer session
- `useAdminAuth` accepts `admin` and `moderator`, exposes role-aware route capabilities, and redirects moderators away from admin-only routes
- Backend authorization is the source of truth. Frontend route guards are only UX controls and must not be treated as security boundaries

Frontend Jest was rerun on 2026-09-12: 33 suites / 104 tests passed, along with TypeScript and ESLint. The production build, zero-vulnerability npm audit, and browser acceptance were recorded on 2026-09-10. Next.js is pinned to 15.5.25, and the lockfile resolves Axios 1.20.0 and PostCSS 8.5.28. Browser acceptance covered 10 public routes at desktop and 375px (20 runs), with no broken images, failed responses, console errors, or horizontal overflow. Keep historical evidence dates distinct from checks actually rerun for a later change.

### Commerce And External Effects

- Resource purchases use integer-valued site coins. A successful paid purchase debits the wallet, writes an immutable ledger entry, creates a paid order, and unlocks the cloud-drive link under transactional and uniqueness protections
- Alipay is a recharge channel, not a direct resource-payment path. Recharge creation and idempotent callback handling are implemented and covered with mocked/local tests; a real sandbox round trip still requires credentials and a reachable callback URL
- Email verification and password-reset endpoints are implemented. SMTP delivery is best-effort: missing credentials or provider failures are logged safely without leaking reset tokens or changing generic API responses
- Newly crawled resources are drafts by default, and crawler synchronization does not overwrite an editor's publish/unpublish decision. Public search returns published resources only
- Crawler deduplication uses batch source lookups, a database source-identity uniqueness constraint, and Redis cross-process leases with renewal and owner-checked release. Moderators can edit only the crawler configuration allowlist, while system-wide settings remain admin-only
- `SEO_AUTO_GENERATE` is a local startup-generation flag. `BAIDU_API_KEY` is optional unless `SEO_SUBMIT_BAIDU=true` is explicitly enabled for a manual submission path; Google/360 flags do not currently have submission implementations

## Current Gaps And Risks

These are the current release boundaries. Do not describe the system as fully production-ready until they are closed or explicitly accepted:

- Validate the complete Compose stack, service health checks, and Grafana/Prometheus/Loki integration with required explicit secrets and public URLs. Docker Hub image-pull timeouts are currently an external deployment-host/network blocker when they prevent startup
- Complete a real Alipay sandbox recharge using `ALIPAY_APP_ID`, `ALIPAY_PRIVATE_KEY`, and `ALIPAY_PUBLIC_KEY`
- Complete real SMTP delivery and Baidu URL-submission checks with valid provider credentials and public network/site configuration
- Google Search Console and 360 submission currently have configuration placeholders but no implemented submission service; confirm that product scope before building them
- Multi-worker crawler schedulers still perform redundant polling even though leases protect correctness. Redis lease ownership and the final database commit are not one atomic transaction, leaving a narrow failure-takeover window
- The crawler source-identity migration intentionally stops when a production database already contains duplicate source rows; clean those rows explicitly before retrying. Direct writes that bypass the API can still cause an entire batch to roll back on a uniqueness conflict

Authentication has one canonical router at `app/api/v1/auth.py`; the former unmounted duplicate router modules were removed. Keep the route-registry regression test when changing authentication wiring.

Use `DEV_PLAN.md` and its latest verification evidence when deciding priority. Treat `PROJECT_TODO.md` only as historical context. Fix security/data-integrity or release-gate issues before cosmetic work unless the user explicitly asks otherwise.

## Engineering Requirements

### Backend Changes

- Keep endpoints and DB access async
- Use FastAPI dependencies for shared auth, DB session access, and permission checks
- Keep configuration in `app/config.py` through `pydantic-settings`; do not scatter raw environment reads across modules
- Use Pydantic schemas for request/response contracts rather than returning raw ORM objects
- Add new routers in `app/api/v1/<module>.py` and register them in `app/api/v1/__init__.py`
- Prefer explicit permission checks using `get_current_admin` for account/financial/system administration and `get_current_staff` for content operations shared with moderators
- Avoid committing secrets, real cloud-drive links, API keys, or production JWT/database credentials
- When changing schema, create/adjust Alembic migrations and verify upgrade/downgrade where practical
- Be careful with `get_db()` auto-commit behavior. If an endpoint needs multi-step transactional control, structure it deliberately and test rollback behavior

### Frontend Changes

- Use `src/lib/api.ts` for backend calls and update the typed wrappers when adding endpoints
- Keep browser-only token/localStorage access inside client components or guarded `typeof window !== 'undefined'` blocks
- Admin UI may hide/show controls based on client auth state, but every sensitive operation must also be protected by backend permissions
- Use the existing component organization and Tailwind style approach
- Keep Chinese as the primary UI language
- Avoid introducing a second data-fetching pattern unless it clearly improves a page. The current codebase mainly uses Axios wrappers and React hooks
- For resource URLs, use slugs for public pages and numeric IDs for admin mutations where the backend expects IDs

### Product And Security Rules

- Paid resource links/extraction codes must not be exposed to unauthenticated users or users who have not purchased the resource
- Never rely on hidden frontend UI as access control for admin or paid-resource features
- Treat orders, payments, and resource delivery as auditable flows. Add backend status fields/logging before building only the page UI
- Do not add mock data to production-facing pages unless it is clearly labeled and isolated as temporary development scaffolding
- Any feature involving payments, emails, SEO submission, or third-party APIs must read credentials from settings/env and fail safely when credentials are absent

## Documentation Notes

- `DEV_PLAN.md` is the current implementation and verification status document
- `PROJECT_TODO.md` preserves the 2026-04-27 audit as a historical snapshot; its unchecked boxes are not the current backlog
- `ibooks.md` is the product requirements reference
- `README.md`, `QUICKSTART.md`, and `DEPLOYMENT.md` are operational/user guidance and should remain consistent with the Compose file and current coin-based purchase flow
- If implementation behavior and docs disagree, trust the code first, then update the docs as part of the change

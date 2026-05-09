# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iBooks is a Chinese-language digital resource marketplace for e-books, video courses, documents, and similar downloadable/cloud-drive resources.

- Backend: Python 3, FastAPI 0.109, SQLAlchemy 2 async ORM, Pydantic v2, PostgreSQL, Redis
- Frontend: Next.js 14 App Router, React 18, TypeScript, Tailwind CSS 3.4
- Infra: Docker Compose for PostgreSQL, Redis, backend, frontend, Prometheus, Grafana, Loki, and Promtail
- Product status: prototype/MVP-level implementation. API and pages exist for many modules, but several business-critical flows are incomplete or mocked. Check `PROJECT_TODO.md` before claiming a feature is production-ready.

## Common Commands

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v
pytest tests/test_auth.py -v
pytest tests/ -v --cov=app

# Alembic migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

Backend local development requires `.env` values for at least `DATABASE_URL`, `REDIS_URL`, and `JWT_SECRET_KEY`. The async PostgreSQL URL must use the `postgresql+asyncpg://` driver. Tests use in-memory SQLite through `sqlite+aiosqlite:///:memory:`.

### Frontend

```bash
cd frontend

npm install
npm run dev
npm run build
npm run lint
npm start
```

Frontend environment variables:

- `NEXT_PUBLIC_API_URL`, default `http://localhost:8000`
- `NEXT_PUBLIC_SITE_URL`, default `http://localhost:3000`

`NEXT_PUBLIC_API_URL` is bundled into browser code. In Docker or production, do not set it to an internal-only host such as `http://backend:8000` unless the browser can resolve that host. Use a public/reverse-proxied API URL for browser access.

### Docker

```bash
docker-compose up -d
docker-compose down
docker-compose logs -f backend
```

Expected local ports from `docker-compose.yml`:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/api/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Loki: `http://localhost:3100`

## Architecture

### Backend

Entry point: `backend/app/main.py`.

Startup flow:

1. `setup_logging()`
2. `init_db()`, which currently calls `Base.metadata.create_all`
3. CORS, performance middleware, and audit middleware are installed according to settings
4. API routers are mounted under `settings.API_V1_PREFIX`, currently `/api/v1`

Request flow:

HTTP request -> CORS -> optional `PerformanceMiddleware` -> optional `AuditMiddleware` -> router -> FastAPI dependencies -> endpoint handler -> async SQLAlchemy session commit/rollback.

Important backend modules:

- `app/api/v1/`: route modules for auth, resources, categories, contacts, FAQs, search, admin, SEO, bulk import, and settings
- `app/api/v1/__init__.py`: central router aggregation. Add new v1 routers here
- `app/models/`: SQLAlchemy ORM models; all inherit from `app.database.Base`
- `app/schemas/`: Pydantic request/response schemas
- `app/dependencies.py`: shared DB and auth dependencies, including current-user and admin checks
- `app/middleware/`: CORS, request audit logging, and performance tracking
- `app/utils/`: security, logging, metrics, SEO helpers, and bulk import utilities
- `app/static_generator/`: sitemap, RSS, robots, and static HTML generation helpers

Database behavior:

- `get_db()` yields an async session, commits after successful request handling, rolls back on exceptions, and closes the session
- Alembic is configured, but there are currently no generated migration files under `backend/alembic/versions`
- Because startup also calls `create_all()`, local development may appear to work even when migrations are missing. For deployment, generate and verify migrations instead of relying on `create_all()`

Testing behavior:

- Existing tests are minimal and backend-only
- Tests use SQLite in memory and create/drop all tables per test fixture
- When changing model constraints, PostgreSQL-specific behavior, authentication, or admin permissions, add focused tests instead of relying only on the current auth tests

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

Authentication:

- Login stores JWT in `localStorage`
- Axios attaches the token as `Authorization: Bearer ...`
- 401 responses clear the token and redirect to `/login` or `/admin/login`
- Backend authorization is the source of truth. Frontend route guards are only UX controls and must not be treated as security boundaries

## Current Gaps And Risks

These are known project-level gaps. Do not describe the system as complete without addressing them.

- Admin login/guard currently does not sufficiently verify admin role on the frontend
- `backend/app/dependencies.py` has a known `get_optional_user` async-call issue listed in `PROJECT_TODO.md`
- Alembic has no committed migration revisions
- Payment, order, and paid-resource delivery flows are not implemented
- Email verification/password reset infrastructure is not implemented, despite email-related model fields/settings
- Several admin pages still use mocked data or incomplete API integration
- Monitoring stack is only partially configured; `docker-compose.yml` references Grafana/Promtail provisioning paths that may not exist
- Frontend has no test suite
- Backend test coverage is very small

Use `PROJECT_TODO.md` as the backlog source when deciding priority. Fix P0 security/data issues before cosmetic work unless the user explicitly asks otherwise.

## Engineering Requirements

### Backend Changes

- Keep endpoints and DB access async
- Use FastAPI dependencies for shared auth, DB session access, and permission checks
- Keep configuration in `app/config.py` through `pydantic-settings`; do not scatter raw environment reads across modules
- Use Pydantic schemas for request/response contracts rather than returning raw ORM objects
- Add new routers in `app/api/v1/<module>.py` and register them in `app/api/v1/__init__.py`
- Prefer explicit permission checks using backend dependencies such as `get_current_admin` for admin-only endpoints
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

- `README.md`, `backend/README.md`, and `frontend/README.md` contain setup guidance but may overstate completion status
- `PROJECT_TODO.md` is the current audit/backlog document dated 2026-04-27
- `ibooks.md` appears to be the product requirements reference
- If implementation behavior and docs disagree, trust the code first, then update the docs as part of the change

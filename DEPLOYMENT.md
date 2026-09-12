# Deployment & Development Guide

This guide covers how to run the project in two modes:
1. **Local Development**: Using SQLite for easy debugging.
2. **Production**: Using PostgreSQL for performance and reliability.

## 1. Local Development (SQLite)

For local debugging, we use SQLite to avoid the overhead of running a full PostgreSQL instance.

### Prerequisites
- Python 3.11+
- Node.js 18.18+ (the Docker image and CI use Node.js 20)
- Redis 7 for the full authentication/readiness flow. Docker is optional only if Redis is provided another way

### Backend Setup
1. **Install Dependencies**:
   ```bash
   cd backend
   # Includes requirements.txt plus pytest, coverage, audit, and Ruff tooling.
   python -m pip install -r requirements-dev.txt
   ```

2. **Configure Environment**:
   Create a `.env` file in `backend/` with the following content:
   ```ini
   # Database (SQLite)
   DATABASE_URL=sqlite+aiosqlite:///./ibooks.db
   
   # Security
   # Local development only; generate a different 32+ character value in production.
   JWT_SECRET_KEY=dev_secret_key
   JWT_ALGORITHM=HS256
   DEBUG=true
   
   # Redis (required for logout blacklisting, password-reset tokens and /health readiness)
   REDIS_URL=redis://127.0.0.1:6379/0

   # Public site URL used in email links and browser return URLs
   SITE_URL=http://localhost:3000
   # Public backend URL used for payment notifications
   API_PUBLIC_URL=http://localhost:8000

   # Keep Alembic as the normal schema path
   SCHEMA_BOOTSTRAP_ENABLED=false
   ```

   For a backend running directly on Windows, keep the explicit `127.0.0.1`
   Redis host. On some machines `localhost` resolves to IPv6 while Redis listens
   only on IPv4, which makes the dependency-aware `/health` probe return 503.
   Docker Compose is different and correctly keeps the internal
   `redis://redis:6379/0` service address.

3. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start Backend**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   API will be available at `http://localhost:8000`.

### Frontend Setup
1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure the browser-facing URLs**:
   ```bash
   cp .env.example .env.local
   ```

   The local values are:
   ```ini
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_SITE_URL=http://localhost:3000
   # Optional server-side rewrite target; defaults to NEXT_PUBLIC_API_URL.
   INTERNAL_API_URL=http://localhost:8000
   ```

3. **Start Frontend**:
   ```bash
   npm run dev -- --hostname 127.0.0.1
   ```
   Frontend will be available at `http://localhost:3000` without exposing the
   development server to the local network.

---

## 2. Production Deployment (PostgreSQL)

For production, we use Docker Compose to orchestrate the full stack including PostgreSQL, Redis, and Monitoring tools.

### Configuration
Copy the root template and fill it before running Compose:

```bash
cp .env.example .env
```

`docker compose` fails fast when the database password, JWT secret, Grafana
password, public URLs, CORS origins, or the explicit Alipay sandbox-mode flag
are missing. Generate independent
secrets (for example with `openssl rand -hex 32`) and configure at least:

```ini
DB_PASSWORD=<random-hex-value>
JWT_SECRET_KEY=<random-value-at-least-32-characters>
GRAFANA_PASSWORD=<independent-random-value>
DEBUG=false

# Public site URL used in email links, SEO URLs and browser return URLs.
SITE_URL=https://your-domain.com
# Public backend URL reachable by Alipay for asynchronous notifications.
API_PUBLIC_URL=https://api.your-domain.com
CORS_ORIGINS=https://your-domain.com
```

`SITE_URL` and `API_PUBLIC_URL` must be externally reachable HTTPS origins in
production and must not end in `/`. Compose passes them to the backend and also
uses them as the frontend image's `NEXT_PUBLIC_SITE_URL` and
`NEXT_PUBLIC_API_URL` build arguments. Because Next.js compiles these public
values into the browser bundle, rebuild the frontend image whenever either URL
changes.

Generated resource HTML is exposed through the frontend origin at
`https://your-domain.com/generated/resources/{slug}.html`. Docker Compose bakes
`http://backend:8000` into the Next.js rewrite as `INTERNAL_API_URL`; non-Compose
builds use `INTERNAL_API_URL` when present and otherwise fall back to
`NEXT_PUBLIC_API_URL`. Generate the files with the staff-only
`POST /api/v1/seo/generate-static-pages` endpoint. These files are auxiliary SEO
artifacts and do not replace the canonical `/resources/{slug}` product pages;
missing files and invalid slugs return `404`.

For a local-only Docker run, explicitly opt into development mode and use the
localhost origins:

```ini
DEBUG=true
SITE_URL=http://localhost:3000
API_PUBLIC_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000
ALIPAY_SANDBOX=true
```

### Host Bindings, Retention, and Log Rotation

All published host ports bind to loopback by default. Keep these defaults when
an authenticated reverse proxy runs on the same host; use `0.0.0.0` only after
an explicit exposure, firewall, and TLS decision:

```ini
FRONTEND_BIND_ADDRESS=127.0.0.1
FRONTEND_PORT=3000
BACKEND_BIND_ADDRESS=127.0.0.1
BACKEND_PORT=8000
MONITORING_BIND_ADDRESS=127.0.0.1
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

PROMETHEUS_RETENTION=15d
LOKI_RETENTION=168h
LOG_MAX_SIZE=10m
LOG_MAX_FILES=5
```

`LOKI_RETENTION` must be at least 24 hours. `LOG_MAX_SIZE` and `LOG_MAX_FILES`
control Docker's `json-file` rotation and do not replace application-level log
retention policies.

### Coin Recharge Payment Configuration

Resources are purchased with internal coins. Third-party payment channels are only used to recharge coins.

For Alipay recharge, configure:

```ini
ALIPAY_APP_ID=your-alipay-app-id
ALIPAY_PRIVATE_KEY=your-rsa-private-key
ALIPAY_PUBLIC_KEY=alipay-rsa-public-key
ALIPAY_SANDBOX=false
```

The platform can browse and purchase resources with existing site coins while
the three Alipay credentials are blank. In that state, creating an Alipay
recharge payment is intentionally unavailable. Configure all three credentials
before enabling or validating the recharge path.

For sandbox testing, set:

```ini
ALIPAY_SANDBOX=true
```

The application selects the matching Alipay gateway from `ALIPAY_SANDBOX`;
`ALIPAY_GATEWAY` is not an application setting. Store PEM values on one line
with literal `\n` separators when using an env file.

The active recharge endpoints are:

```text
POST /api/v1/recharge/alipay/create
POST /api/v1/recharge/alipay/notify
```

Legacy resource-order payment endpoints are intentionally not exposed.

### Email and SEO Integrations

Email verification and password-reset delivery require all sender credentials:

```ini
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=noreply@your-domain.com
EMAIL_USERNAME=your-smtp-user
EMAIL_PASSWORD=your-smtp-password
EMAIL_USE_TLS=true
```

The API can start without SMTP credentials, but registration verification and
password-reset messages will not be delivered. Missing credentials and provider
failures are handled as observable best-effort failures rather than startup
requirements.

Baidu submission is opt-in. Leave it disabled when no key is available:

```ini
SEO_AUTO_GENERATE=true
SEO_SUBMIT_BAIDU=false
BAIDU_API_KEY=
```

`SEO_AUTO_GENERATE=true` refreshes only the local `sitemap.xml`, `rss.xml`, and
`robots.txt` files during backend startup; it never submits URLs externally,
and generated resource HTML remains an explicit staff action.

Set `SEO_SUBMIT_BAIDU=true` only together with a valid `BAIDU_API_KEY`.

### Running with Docker Compose
```bash
docker compose config --quiet
docker compose up -d --build
```

This will start:
- **Backend**: FastAPI service
- **Frontend**: Next.js service
- **Postgres**: Database
- **Redis**: Cache
- **Exporters**: PostgreSQL and Redis metrics collectors
- **Monitoring**: Prometheus, Grafana, Loki, and Promtail

PostgreSQL, Redis, Loki, Promtail, and both exporters are only reachable on the
private Compose network. Frontend, backend, Prometheus, and Grafana bind to
`127.0.0.1` by default, so none of their published ports are directly exposed
on public interfaces. Put an authenticated TLS reverse proxy in front of any UI
or API that must be accessed remotely. The backend and frontend application
images run as non-root users.

The backend exposes two probes with different semantics:

- `/live` confirms only that the API process can respond.
- `/health` checks PostgreSQL and Redis and is the dependency-aware readiness
  endpoint used by Compose.

### Persistent Data, Logs, and Backups

Compose uses named volumes for PostgreSQL, Redis, backend file logs, generated
SEO files, uploads, Prometheus, Grafana, and Loki. In particular, Promtail mounts
`backend_logs` read-only; Compose does not write backend file logs into a host
`logs/backend/` directory. Use:

```bash
docker compose logs -f backend
```

for normal service diagnostics. Configure regular PostgreSQL backups with
`pg_dump`, and separately protect user uploads and any generated artifacts that
must survive a host loss. `docker compose down -v` deletes all named volumes and
must not be used as an ordinary stop or rollback command.

The current Loki configuration uses TSDB schema v13 with compactor retention and
writes to the new `loki_tsdb_data` volume. It deliberately does not reuse an old
`loki_data` volume created by the former `boltdb-shipper` layout. Back up or
export the old volume before upgrading; after confirming that its logs are no
longer needed, clean it up manually. Do not use `docker compose down -v` as a
Loki migration or cleanup shortcut because it also removes all current named
volumes.

## 3. Switching Modes

To switch between modes, simply update the `DATABASE_URL` in your `.env` file.

- **SQLite**: `sqlite+aiosqlite:///./ibooks.db`
- **PostgreSQL**: `postgresql+asyncpg://user:pass@host/dbname`

The application code automatically detects the database type and configures the connection engine accordingly.

## 4. Release Readiness and Rollback

Recorded code-quality baseline:

- Backend: `292 passed` with `72.42%` total coverage (approximately `72%`).
  Ruff, `pip check`, and `pip-audit` pass, and the dependency audit reports no
  known vulnerabilities.
- Database: a fresh database completes `upgrade -> downgrade -1 -> upgrade`,
  and `alembic check` reports no pending schema changes.
- Frontend: Next.js `15.5.25`, Jest `33 suites / 104 tests passed`, TypeScript,
  ESLint, the full production build, and `npm audit` pass, and `npm audit`
  reports zero known vulnerabilities.
- Browser regression: 10 public routes at desktop and 375px widths (20 runs)
  pass HTTP, console-error, failed-response, broken-image, and horizontal-
  overflow checks.

These results do not replace the environment-specific checks below.

Current client and operator contracts:

- `GET /api/v1/resources/{slug}/access` is a side-effect-free authorization
  check returning `has_access`. Delivery data is returned only by
  `POST /api/v1/resources/{slug}/download`, which atomically increments the
  download counter.
- Anonymous settings responses are restricted to approved presentation keys,
  and each item contains only `key` and `value`; administrative metadata is not
  exposed.
- Refresh-token rotation tolerates another browser tab replacing the stored
  credentials. A stale request or failed old refresh must not clear the newer
  session.
- `POST /api/v1/seo/generate-all` waits for sitemap, RSS, and robots generation.
  Success returns the generated file list; a partial failure returns a safe 500
  detail with separate generated and failed file lists.
- Public FAQ, contact, and category views distinguish upstream failure from a
  valid empty result. `GET /api/v1/admin/users` returns the standard paginated
  object with `items`, `total`, `page`, `page_size`, and `pages`.

Before a release:

1. Confirm `docker compose config --quiet` succeeds, start the stack, and verify every service reports healthy with `docker compose ps`.
2. Run backend tests, frontend tests, TypeScript checks, and a production frontend build.
3. Apply migrations with `alembic upgrade head`, then verify `/health`, `/metrics`, sitemap, and robots endpoints.
4. Run one crawler sync in the admin panel and confirm the imported count and deduplication behavior.
5. Confirm `DEBUG=false`, real HTTPS public URLs, and the required database/JWT/Grafana secrets are present.
6. If SMTP, Alipay recharge, or search-engine submission will be offered, configure and validate that integration's credentials; `BAIDU_API_KEY` is required only when `SEO_SUBMIT_BAIDU=true`.
7. Validate PostgreSQL backup and restore, protect the uploads volume, and review Prometheus/Loki retention before production sign-off.

Rollback procedure:

1. Stop traffic at the reverse proxy and keep the database volume intact.
2. Deploy the previous application image and restart `backend` and `frontend`.
3. Do not downgrade migrations automatically. Restore a database backup only after verifying migration compatibility.
4. Recheck `/health`, login, resource access, wallet balance, and payment callback endpoints before reopening traffic.

This repository has not yet completed full production-style Compose and
monitoring runtime acceptance. External validation also remains required before
production sign-off for the integrations that will be enabled: Alipay sandbox
credentials and a reachable callback URL for recharge, SMTP credentials for
real mail delivery, and Baidu credentials for live URL submission. Docker Hub
image-pull timeouts are an external deployment-host/network blocker when they
prevent the full stack from starting; resolve that connectivity or configure a
trusted mirror before repeating runtime acceptance. Google Search Console and
360 submission remain product-scope decisions and do not currently have an
implemented submission service.

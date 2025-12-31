# Deployment & Development Guide

This guide covers how to run the project in two modes:
1. **Local Development**: Using SQLite for easy debugging.
2. **Production**: Using PostgreSQL for performance and reliability.

## 1. Local Development (SQLite)

For local debugging, we use SQLite to avoid the overhead of running a full PostgreSQL instance.

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (optional, for Redis/Prometheus)

### Backend Setup
1. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Create a `.env` file in `backend/` with the following content:
   ```ini
   # Database (SQLite)
   DATABASE_URL=sqlite+aiosqlite:///./ibooks.db
   
   # Security
   JWT_SECRET=dev_secret_key
   JWT_ALGORITHM=HS256
   
   # Redis (Optional, can disable in code or run via Docker)
   REDIS_URL=redis://localhost:6379
   ```

3. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start Backend**:
   ```bash
   uvicorn app.main:app --reload
   ```
   API will be available at `http://localhost:8000`.

### Frontend Setup
1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start Frontend**:
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000`.

---

## 2. Production Deployment (PostgreSQL)

For production, we use Docker Compose to orchestrate the full stack including PostgreSQL, Redis, and Monitoring tools.

### Configuration
Ensure your `.env` file (or environment variables) is configured for PostgreSQL:

```ini
# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://admin:${DB_PASSWORD}@postgres/resource_marketplace
```

### Running with Docker Compose
```bash
docker-compose up -d --build
```

This will start:
- **Backend**: FastAPI service
- **Frontend**: Next.js service
- **Postgres**: Database
- **Redis**: Cache
- **Nginx**: Reverse proxy
- **Monitoring**: Prometheus, Grafana, Loki

### Database Backups
PostgreSQL data is persisted in the `postgres_data` volume. Regular backups should be configured using `pg_dump`.

## 3. Switching Modes

To switch between modes, simply update the `DATABASE_URL` in your `.env` file.

- **SQLite**: `sqlite+aiosqlite:///./ibooks.db`
- **PostgreSQL**: `postgresql+asyncpg://user:pass@host/dbname`

The application code automatically detects the database type and configures the connection engine accordingly.

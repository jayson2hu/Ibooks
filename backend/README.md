# Digital Resource Marketplace - Backend

FastAPI backend for the Digital Resource Marketplace.

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

## Quick Start

### 1. Create Environment File

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start Server

```bash
uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Prometheus Metrics: http://localhost:8000/metrics

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
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Environment Variables

See `.env.example` for all available configuration options.

## Docker

```bash
docker build -t resource-marketplace-backend .
docker run -p 8000:8000 --env-file .env resource-marketplace-backend
```

## Testing

```bash
pytest tests/ -v --cov=app
```

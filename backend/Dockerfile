FROM python:3.11-slim

WORKDIR /app

ARG APP_UID=10001
ARG APP_GID=10001

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "${APP_GID}" app \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" \
        --home-dir /home/app --create-home --shell /usr/sbin/nologin app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create application-owned runtime directories before named volumes are mounted.
RUN mkdir -p /app/logs /app/static_pages /app/uploads \
    && chown -R app:app /app/logs /app/static_pages /app/uploads

USER app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

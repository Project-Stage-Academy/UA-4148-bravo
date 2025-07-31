# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Stage 1: build dependencies
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update -q && \
    apt-get install -y -q --no-install-recommends --no-install-suggests \
        libpq-dev gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install pip requirements
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --user --no-cache-dir -r requirements.txt

# Stage 2: production image
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/root/.local/bin:$PATH

# Install system dependencies, curl and dos2unix
RUN apt-get update -q && \
    apt-get install -y -q --no-install-recommends --no-install-suggests \
        curl netcat-openbsd postgresql-client dos2unix && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only needed files
COPY --from=builder /root/.local /root/.local
COPY . .

# Copy entrypoint script and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh

# Expose the port Django will run on
EXPOSE 8000

# Use the entrypoint script as the container's entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# --------------------------------------------------
# 📝 Required environment variables (loaded from .env)
#
# These are read in settings.py via python-decouple:
#
#   SECRET_KEY     - Django secret key
#   DEBUG          - Set to "False" in production
#   DB_NAME        - PostgreSQL database name
#   DB_USER        - PostgreSQL username
#   DB_PASSWORD    - PostgreSQL password
#   DB_HOST        - PostgreSQL host (e.g., "db" for Docker)
#   DB_PORT        - PostgreSQL port (default: 5432)
#
# These variables should be defined in a `.env` file, which is automatically read by Docker Compose.
# --------------------------------------------------

# Run server for production
CMD ["db", "gunicorn", "--log-level=debug", "core.wsgi:application", "--bind=0.0.0.0:8000", "--workers=3", "--timeout=120"]

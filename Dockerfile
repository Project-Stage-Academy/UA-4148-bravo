# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies and curl
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     libpq-dev gcc curl netcat-openbsd postgresql-client \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install pip requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy Django project code
COPY . .

# Copy entrypoint script and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

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
CMD ["db", "gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers=3", "--timeout=120"]

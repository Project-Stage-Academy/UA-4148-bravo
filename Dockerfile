# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl netcat-openbsd postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project code
COPY . .

# Expose the port Django will run on
EXPOSE 8000

# Run server for production
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]

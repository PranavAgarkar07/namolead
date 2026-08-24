#!/bin/bash
set -euo pipefail

# Pull latest changes
git pull --ff-only origin main

# Run migrations
python manage.py migrate --noinput

# Collect static
python manage.py collectstatic --noinput

# Restart app
docker compose up -d --build

# Health check
curl -fsS http://localhost:8000/health/ || exit 1
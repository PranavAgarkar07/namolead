# NamoLead Opportunities

Wagtail CMS site: editors publish opportunities (image + paragraph + apply link),
outbound clicks tracked via /go/<slug>/, exclusive posts gated behind an
Instagram-follow soft gate + email magic-link verification, staff analytics at
/analytics/.

## Local dev

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py seed_demo
    python manage.py createsuperuser   # editor + analytics access
    python manage.py runserver

Editor UI: http://127.0.0.1:8000/admin/  ·  Dashboard: /analytics/

## Deploy (EC2 free tier or Railway)

    docker compose up -d --build
    docker compose run web python manage.py migrate
    docker compose run web python manage.py seed_demo
    docker compose run web python manage.py createsuperuser

A `.env` file must exist with POSTGRES_PASSWORD set before `docker compose up`
(copy .env.example and fill it in).

Health check: GET /health/ returns 200 `{"status":"ok","database":"ok"}` when the
app and database are healthy; 503 otherwise. The container HEALTHCHECK hits it.

## Rollback

1. `git fetch origin && git log --oneline origin/main` to pick the previous good SHA
2. `git checkout <previous-sha>` (detached HEAD is fine on the server)
3. `docker compose up -d --build --force-recreate`
4. Verify: `curl -i http://localhost:8000/health/` returns 200
5. If a schema migration was part of the broken release, restore the DB from the
   S3 backup first (see below) — never roll back code across a non-reversible
   migration.

## Backups

Nightly cron on the host: `pg_dump` + media tar → S3 bucket (`namolead-backups`).
Restore: `aws s3 cp s3://namolead-backups/<date>/db.sql / - | docker compose exec -T db psql -U namolead -d namolead`

Production env vars (see .env.example): DJANGO_SECRET_KEY, DEBUG=False,
ALLOWED_HOSTS, IP_HASH_SALT, DATABASE_URL (Postgres), POSTGRES_PASSWORD, and
EMAIL_* (unlock emails; default console backend prints to the server log).
Media files live on the `media` volume; swap to R2 via django-storages when the
site grows. HTTPS via Caddy/certbot or the platform's TLS terminator.

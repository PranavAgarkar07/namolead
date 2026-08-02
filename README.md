# NamoLead Opportunities

Wagtail CMS site: editors publish opportunities (image + paragraph + apply link),
outbound clicks tracked via /go/<slug>/, exclusive posts gated behind an
Instagram-follow soft gate, staff analytics at /analytics/.

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

Production env vars (see .env.example): DJANGO_SECRET_KEY, DEBUG=False,
ALLOWED_HOSTS, IP_HASH_SALT, DATABASE_URL (Postgres), POSTGRES_PASSWORD.
Media files live on the `media` volume; swap to R2 via django-storages when the
site grows. HTTPS via Caddy/certbot or the platform's TLS terminator.

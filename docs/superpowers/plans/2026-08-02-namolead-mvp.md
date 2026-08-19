# NamoLead Opportunities MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Wagtail-powered opportunity site where non-technical editors publish image + paragraph + apply-link posts, visitors' clicks and views are tracked, exclusive posts unlock behind an Instagram-follow soft gate, and staff see a Chart.js analytics dashboard.

**Architecture:** Single Django project, two apps. `opportunities` owns CMS models (Wagtail Page subclasses) and user-facing views (apply redirect, pageview beacon, gate unlock). `tracking` owns the three event models (ClickEvent, PageView, Unlock), the staff-only analytics dashboard, and the IP-hashing util. All cross-app FKs use string references (`'opportunities.OpportunityPage'`) so no module-level import cycles exist.

**Tech Stack:** Django ~=5.2 (LTS), Wagtail ~=6.4 (LTS), django-environ, whitenoise, gunicorn, Tailwind + Chart.js via CDN. SQLite for dev, Postgres via env var in prod. No DRF, no Django-Q2, no Redis, no R2 (deferred deliberately).

## Global Constraints

- Python 3.12+, Django `~=5.2`, Wagtail `~=6.4` — no other pip dependencies.
- No raw IPs stored anywhere — only `sha256(IP_HASH_SALT + ':' + ip)`; IP missing → `''`.
- Wagtail admin (`/admin/`) is the ONLY editor surface; never expose Django admin to non-staff.
- Analytics dashboard is staff-only (`staff_member_required`), reusing Wagtail's admin login via `LOGIN_URL = '/admin/login/'`.
- Outbound links only ever go through `/go/<slug>/`; never link `apply_url` directly in templates.
- Templates use `{% image %}` tag from `wagtailimages_tags` for featured images.
- The seed command must be idempotent (early-return if already seeded).

---

### Task 1: Scaffold — project, apps, settings, urls, git

**Files:**
- Create: `requirements.txt`, `.gitignore`, `.env.example`, `namolead/settings.py`, `namolead/urls.py`, `opportunities/__init__.py`, `tracking/__init__.py`, `manage.py` (via startproject/startapp)
- Modify: `namolead/settings.py` (Wagtail + whitenoise + env wiring)

- [ ] **Step 1: Create venv, install deps, scaffold project**

```bash
cd /home/pranav/Desktop/projects/django
git init
python3 -m venv .venv && source .venv/bin/activate
pip install "Django~=5.2" "wagtail~=6.4" django-environ whitenoise gunicorn
pip freeze > requirements.txt
django-admin startproject namolead .
python manage.py startapp opportunities
python manage.py startapp tracking
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
.venv/
__pycache__/
*.pyc
db.sqlite3
.env
staticfiles/
media/
.DS_Store
```

- [ ] **Step 3: Write `.env.example`**

```env
DJANGO_SECRET_KEY=change-me
DEBUG=True
IP_HASH_SALT=change-me-too
DATABASE_URL=   # leave blank in dev (SQLite); set postgres://... in prod
```

- [ ] **Step 4: Rewrite `namolead/settings.py`**

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-key")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = ["*"] if DEBUG else env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "opportunities",
    "tracking",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "namolead.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "namolead.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

WAGTAIL_SITE_NAME = "NamoLead Opportunities"
LOGIN_URL = "/admin/login/"

IP_HASH_SALT = env("IP_HASH_SALT", default="dev-salt")
```

- [ ] **Step 5: Rewrite `namolead/urls.py`**

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("", include(("opportunities.urls", "opportunities"), namespace="opportunities")),
    path("", include(("tracking.urls", "tracking"), namespace="tracking")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [path("", include(wagtail_urls))]
```

- [ ] **Step 6: Verify + commit**

```bash
python manage.py migrate
python manage.py check
python manage.py runserver 2>/dev/null & sleep 3; curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/admin/login/; kill %1
# expected: 200
```

```bash
git add -A
git commit -m "chore: scaffold Django + Wagtail project with opportunities and tracking apps"
```

---

### Task 2: CMS models, templates, seed command

**Files:**
- Create: `opportunities/models.py`, `opportunities/urls.py` (empty stub), `opportunities/management/__init__.py`, `opportunities/management/commands/__init__.py`, `opportunities/management/commands/seed_demo.py`, `templates/base.html`, `opportunities/templates/opportunities/opportunity_index_page.html`, `opportunities/templates/opportunities/opportunity_page.html`, `opportunities/tests.py`
- Modify: `opportunities/apps.py` (nothing — default fine)

**Interfaces:**
- Produces: `OpportunityIndexPage(Page)` — `max_count=1`, `subpage_types=['OpportunityPage']`, `get_context()` returns `opportunities`, `categories`, `active_category`. `OpportunityPage(Page)` with fields `category`, `organization`, `short_description`, `featured_image`, `apply_url`, `is_exclusive`. Slug auto-derived from title by Wagtail.

- [ ] **Step 1: Write failing tests**

```python
# opportunities/tests.py
from django.test import TestCase
from wagtail.models import Page, Site

from .models import OpportunityIndexPage, OpportunityPage


def seed_site():
    root = Page.objects.filter(depth=1).first()
    index = root.add_child(instance=OpportunityIndexPage(title="Home"))
    site = Site.objects.first()
    site.root_page = index
    site.save()
    return index


def publish(parent, **kwargs):
    page = parent.add_child(instance=OpportunityPage(**kwargs))
    page.save_revision().publish()
    return page


class OpportunityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.index = seed_site()
        cls.intern = publish(
            cls.index,
            title="Internship A",
            category="internship",
            organization="Acme",
            short_description="Great internship",
            apply_url="https://example.com/apply",
        )
        cls.scholar = publish(
            cls.index,
            title="Scholarship B",
            category="scholarship",
            short_description="Funded study",
            apply_url="https://example.com/scholarship",
        )

    def test_index_lists_published_posts(self):
        response = self.client.get("/")
        self.assertContains(response, "Internship A")
        self.assertContains(response, "Scholarship B")

    def test_index_filters_by_category(self):
        response = self.client.get("/", {"category": "scholarship"})
        self.assertContains(response, "Scholarship B")
        self.assertNotContains(response, "Internship A")

    def test_detail_page_renders(self):
        response = self.client.get("/internship-a/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Great internship")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test opportunities -v 2`
Expected: FAIL — module/import errors (models don't exist yet).

- [ ] **Step 3: Write models**

```python
# opportunities/models.py
from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page


class Category(models.TextChoices):
    INTERNSHIP = "internship", "Internship"
    SIMULATION = "simulation", "Virtual Job Simulation"
    GOVT_DEFENSE = "govt-defense", "Govt / Defense"
    SCHOLARSHIP = "scholarship", "Scholarship"
    HACKATHON = "hackathon", "Hackathon"
    CERTIFICATION = "certification", "Certification"


class OpportunityIndexPage(Page):
    max_count = 1
    subpage_types = ["OpportunityPage"]

    def get_context(self, request):
        ctx = super().get_context(request)
        category = request.GET.get("category", "")
        qs = OpportunityPage.objects.child_of(self).live().order_by("-first_published_at")
        if category in Category.values:
            qs = qs.filter(category=category)
        ctx["opportunities"] = qs
        ctx["categories"] = Category.choices
        ctx["active_category"] = category
        return ctx


class OpportunityPage(Page):
    parent_page_types = ["OpportunityIndexPage"]
    subpage_types = []

    category = models.CharField(max_length=32, choices=Category.choices, default=Category.INTERNSHIP)
    organization = models.CharField(max_length=128, blank=True)
    short_description = models.TextField(
        max_length=2000,
        blank=True,
        help_text="The main paragraph shown on the card and post page.",
    )
    featured_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Shown at the top of the post.",
    )
    apply_url = models.URLField(help_text="Real destination URL. Visitors are routed via /go/<slug>/ for tracking.")
    is_exclusive = models.BooleanField(
        default=False,
        help_text="Hidden behind the Follow-on-Instagram gate. Exclusivity is a soft gate, not real access control.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("category"),
        FieldPanel("organization"),
        FieldPanel("featured_image"),
        FieldPanel("short_description"),
        FieldPanel("apply_url"),
        FieldPanel("is_exclusive"),
    ]

    def get_context(self, request):
        ctx = super().get_context(request)
        ctx["unlocked"] = request.session.get(f"unlocked_{self.pk}", False)
        return ctx
```

- [ ] **Step 4: Migrations + urls stub**

```bash
python manage.py makemigrations opportunities
python manage.py migrate
```

```python
# opportunities/urls.py (stub for now, populated in Task 3)
urlpatterns = []
```

- [ ] **Step 5: Write templates**

```html
<!-- templates/base.html -->
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}NamoLead Opportunities{% endblock %}</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 text-gray-900">
<nav class="bg-white border-b px-6 py-4">
  <a href="/" class="font-bold text-lg">NamoLead Opportunities</a>
</nav>
<main class="max-w-3xl mx-auto px-6 py-8">
{% if messages %}
  {% for m in messages %}<div class="bg-yellow-100 border border-yellow-300 text-yellow-900 px-4 py-2 rounded mb-4">{{ m }}</div>{% endfor %}
{% endif %}
{% block content %}{% endblock %}
</main>
</body>
</html>
```

```html
<!-- opportunities/templates/opportunities/opportunity_index_page.html -->
{% extends "base.html" %}
{% load wagtailimages_tags %}

{% block content %}
<h1 class="text-2xl font-bold mb-4">Opportunities</h1>

<form method="get" class="mb-6">
  <label for="category" class="mr-2 text-sm">Category</label>
  <select name="category" id="category" class="border rounded px-3 py-2">
    <option value="">All</option>
    {% for value, label in categories %}
      <option value="{{ value }}" {% if value == active_category %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
  </select>
  <button type="submit" class="bg-blue-600 text-white rounded px-4 py-2 ml-2">Filter</button>
</form>

<div class="space-y-4">
  {% for opp in opportunities %}
    <a href="{% pageurl opp %}" class="block bg-white border rounded-lg p-4 hover:shadow">
      {% image opp.featured_image width-800 as card_img %}
      {% if card_img %}<img src="{{ card_img.url }}" class="rounded-md mb-2 h-40 w-full object-cover" alt="">{% endif %}
      <div class="text-xs text-gray-500 uppercase mb-1">{{ opp.get_category_display }}{% if opp.organization %} · {{ opp.organization }}{% endif %}</div>
      <h2 class="font-semibold">{{ opp.title }}</h2>
      <p class="text-sm text-gray-600">{{ opp.short_description|truncatechars:200 }}</p>
    </a>
  {% empty %}
    <p>No opportunities yet.</p>
  {% endfor %}
</div>
{% endblock %}
```

```html
<!-- opportunities/templates/opportunities/opportunity_page.html -->
{% extends "base.html" %}
{% load wagtailimages_tags %}

{% block title %}{{ page.title }} · NamoLead{% endblock %}

{% block content %}
{% image page.featured_image width-800 as hero %}
{% if hero %}<img src="{{ hero.url }}" class="rounded-lg w-full mb-4" alt="">{% endif %}
<h1 class="text-2xl font-bold">{{ page.title }}</h1>
<p class="text-sm text-gray-500 mb-4">
  {{ page.get_category_display }}{% if page.organization %} · {{ page.organization }}{% endif %}
</p>
<p class="mb-6 whitespace-pre-line">{{ page.short_description }}</p>

<img src="{% url 'opportunities:pageview' page.slug %}" width="1" height="1" alt="">

{% if page.is_exclusive and not unlocked %}
<div class="border-2 border-dashed border-blue-300 bg-blue-50 rounded-lg p-6 text-center">
  <p class="font-semibold mb-2">This post is exclusive to the NamoLead community</p>
  <ol class="text-sm text-left mx-auto max-w-md mb-4 list-decimal list-inside">
    <li>Follow <a href="https://instagram.com/namolead" target="_blank" class="text-blue-600 underline">@namolead</a> on Instagram</li>
    <li>Enter your email and press Unlock</li>
  </ol>
  <form method="post" action="{% url 'opportunities:unlock' page.slug %}" class="flex gap-2 max-w-md mx-auto">
    {% csrf_token %}
    <input type="email" name="email" required class="flex-1 border rounded px-3 py-2" placeholder="you@example.com">
    <button type="submit" class="bg-blue-600 text-white rounded px-4 py-2">I've followed — Unlock</button>
  </form>
  <p class="text-xs text-gray-500 mt-3">Instagram follows can't be verified automatically — we trust you.</p>
</div>
{% else %}
<a href="{% url 'opportunities:go' page.slug %}" class="inline-block bg-blue-600 text-white font-semibold rounded-lg px-6 py-3">Apply now</a>
{% endif %}
{% endblock %}
```

- [ ] **Step 6: Write seed command**

```python
# opportunities/management/commands/seed_demo.py
from django.core.management.base import BaseCommand
from wagtail.models import Page, Site

from opportunities.models import OpportunityIndexPage, OpportunityPage


class Command(BaseCommand):
    help = "Create the index page at / and two demo posts."

    def handle(self, *args, **options):
        if OpportunityIndexPage.objects.exists():
            self.stdout.write("Already seeded.")
            return
        root = Page.objects.filter(depth=1).first()
        index = root.add_child(instance=OpportunityIndexPage(title="Home"))
        site = Site.objects.first()
        site.root_page = index
        site.save()

        demo = [
            dict(
                title="Google Summer of Code",
                category="internship",
                organization="Google",
                short_description="Paid remote internship writing open-source code. Apply before the deadline.",
                apply_url="https://summerofcode.withgoogle.com/",
                is_exclusive=False,
            ),
            dict(
                title="Forage: JPMorgan Virtual Simulation",
                category="simulation",
                organization="Forage",
                short_description="Free 5-hour virtual job simulation. Exclusive details unlocked below.",
                apply_url="https://www.theforage.com/",
                is_exclusive=True,
            ),
        ]
        for data in demo:
            page = index.add_child(instance=OpportunityPage(**data))
            page.save_revision().publish()

        self.stdout.write(self.style.SUCCESS("Seeded. Create an editor: python manage.py createsuperuser"))
```

- [ ] **Step 7: Run tests, verify all pass**

```bash
python manage.py test opportunities -v 2
```

- [ ] **Step 8: Verify seed works end-to-end**

```bash
python manage.py seed_demo
python manage.py seed_demo   # must print "Already seeded."
python manage.py runserver 2>/dev/null & sleep 3; curl -s http://127.0.0.1:8000/ | grep -c "Google Summer of Code"; kill %1
# expected: 1
```

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: opportunity CMS models, templates, and seed command"
```

---

### Task 3: Tracking — models, redirect, beacon, gate unlock

**Files:**
- Create: `tracking/models.py`, `tracking/utils.py`, `tracking/urls.py`, `tracking/tests.py`
- Modify: `opportunities/urls.py`, `opportunities/views.py`

**Interfaces:**
- Consumes: `OpportunityPage.slug`, `OpportunityPage.apply_url`, `OpportunityPage.is_exclusive`, `OpportunityPage.get_url(request)`, `OpportunityPage.pk`.
- Produces: `ClickEvent(opportunity FK, timestamp, referrer, user_agent, hashed_ip, utm_source)`, `PageView(opportunity FK, timestamp, hashed_ip)`, `Unlock(opportunity FK, email, hashed_ip, timestamp)`, `hash_ip(request) -> str`, views `go_redirect`, `pageview`, `unlock`.

- [ ] **Step 1: Write failing tests**

```python
# tracking/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.models import Page, Site

from opportunities.models import OpportunityIndexPage, OpportunityPage
from .models import ClickEvent, PageView, Unlock


def seed_site():
    root = Page.objects.filter(depth=1).first()
    index = root.add_child(instance=OpportunityIndexPage(title="Home"))
    site = Site.objects.first()
    site.root_page = index
    site.save()
    return index


class TrackingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        index = seed_site()
        cls.opp = index.add_child(
            instance=OpportunityPage(
                title="Internship A",
                category="internship",
                short_description="Great internship",
                apply_url="https://example.com/apply",
            )
        )
        cls.opp.save_revision().publish()
        cls.exclusive = index.add_child(
            instance=OpportunityPage(
                title="Exclusive C",
                category="internship",
                short_description="Secret",
                apply_url="https://example.com/secret",
                is_exclusive=True,
            )
        )
        cls.exclusive.save_revision().publish()

    def test_go_redirect_logs_click_and_302s(self):
        response = self.client.get("/go/internship-a/?utm_source=whatsapp")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://example.com/apply")
        self.assertEqual(ClickEvent.objects.count(), 1)
        self.assertEqual(ClickEvent.objects.first().utm_source, "whatsapp")

    def test_go_unknown_slug_404s(self):
        self.assertEqual(self.client.get("/go/nope/").status_code, 404)

    def test_invalid_source_falls_back_to_direct(self):
        self.client.get("/go/internship-a/?utm_source=spam")
        self.assertEqual(ClickEvent.objects.first().utm_source, "direct")

    def test_pageview_beacon_logs(self):
        response = self.client.get("/track/view/internship-a/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PageView.objects.count(), 1)

    def test_exclusive_gate_blocks_then_unlocks(self):
        response = self.client.get("/exclusive-c/")
        self.assertNotContains(response, "Apply now")
        self.assertContains(response, "Unlock")

        response = self.client.post("/unlock/exclusive-c/", {"email": "a@b.com"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Unlock.objects.filter(email="a@b.com").count(), 1)

        response = self.client.get("/exclusive-c/")
        self.assertContains(response, "Apply now")

    def test_invalid_email_rejected_no_unlock_created(self):
        self.client.post("/unlock/exclusive-c/", {"email": "not-an-email"})
        self.assertEqual(Unlock.objects.count(), 0)

    def test_analytics_requires_staff(self):
        self.assertEqual(self.client.get("/analytics/").status_code, 302)
        User = get_user_model()
        user = User.objects.create_user("staff", password="x", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get("/analytics/").status_code, 200)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test tracking -v 2`
Expected: FAIL — imports/views don't exist.

- [ ] **Step 3: Write models + utils**

```python
# tracking/models.py
from django.db import models


class ClickEvent(models.Model):
    opportunity = models.ForeignKey(
        "opportunities.OpportunityPage", null=True, on_delete=models.SET_NULL, related_name="clicks"
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    referrer = models.CharField(max_length=255, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    hashed_ip = models.CharField(max_length=64, blank=True)
    utm_source = models.CharField(max_length=32, blank=True, default="direct")


class PageView(models.Model):
    opportunity = models.ForeignKey(
        "opportunities.OpportunityPage", null=True, on_delete=models.SET_NULL, related_name="views"
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    hashed_ip = models.CharField(max_length=64, blank=True)


class Unlock(models.Model):
    opportunity = models.ForeignKey(
        "opportunities.OpportunityPage", null=True, on_delete=models.SET_NULL, related_name="unlocks"
    )
    email = models.EmailField()
    hashed_ip = models.CharField(max_length=64, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
```

```python
# tracking/utils.py
import hashlib

from django.conf import settings


def hash_ip(request):
    ip = request.META.get("REMOTE_ADDR", "")
    if not ip:
        return ""
    return hashlib.sha256(f"{settings.IP_HASH_SALT}:{ip}".encode()).hexdigest()
```

- [ ] **Step 4: Write views + urls**

```python
# opportunities/views.py
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from .models import OpportunityPage

VALID_SOURCES = {"whatsapp", "instagram", "direct"}


def go_redirect(request, slug):
    page = OpportunityPage.objects.filter(slug=slug).first()
    if page is None:
        raise Http404
    from tracking.models import ClickEvent
    from tracking.utils import hash_ip

    source = request.GET.get("utm_source", "direct")
    if source not in VALID_SOURCES:
        source = "direct"
    ClickEvent.objects.create(
        opportunity=page,
        referrer=request.META.get("HTTP_REFERER", "")[:255],
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
        hashed_ip=hash_ip(request),
        utm_source=source,
    )
    return HttpResponseRedirect(page.apply_url)


def pageview(request, slug):
    page = OpportunityPage.objects.filter(slug=slug).first()
    if page is not None:
        from tracking.models import PageView
        from tracking.utils import hash_ip

        PageView.objects.create(opportunity=page, hashed_ip=hash_ip(request))
    return HttpResponse(status=200)


def unlock(request, slug):
    page = get_object_or_404(OpportunityPage, slug=slug)
    if not page.is_exclusive:
        return redirect(page.get_url(request))
    email = request.POST.get("email", "").strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Enter a valid email address.")
        return redirect(page.get_url(request))
    from tracking.models import Unlock
    from tracking.utils import hash_ip

    Unlock.objects.create(opportunity=page, email=email, hashed_ip=hash_ip(request))
    request.session[f"unlocked_{page.pk}"] = True
    messages.success(request, "Unlocked! Follow @namolead on Instagram for more.")
    return HttpResponseRedirect(page.get_url(request))
```

```python
# opportunities/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("go/<slug:slug>/", views.go_redirect, name="go"),
    path("unlock/<slug:slug>/", views.unlock, name="unlock"),
    path("track/view/<slug:slug>/", views.pageview, name="pageview"),
]
```

```python
# tracking/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("analytics/", views.dashboard, name="analytics"),
]
```

- [ ] **Step 5: Migrate + run tests**

```bash
python manage.py makemigrations tracking
python manage.py migrate
python manage.py test tracking -v 2
# expected: 7 passed
python manage.py test -v 2
# expected: all 10 pass
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: click/pageview tracking, go-redirect, and soft-gate unlock"
```

---

### Task 4: Analytics dashboard

**Files:**
- Create: `tracking/views.py`, `tracking/templates/tracking/dashboard.html`

**Interfaces:**
- Consumes: `ClickEvent`, `PageView`, `Unlock` from Task 3.
- Produces: `dashboard(request)` — staff-only; renders `tracking/dashboard.html` with context keys: `totals` (`clicks`, `views`, `unlocks`, `ctr`), `per_post` (list of `title`, `clicks`, `views`, `ctr`), `per_category` (`name`, `clicks`), `by_source` (`source`, `clicks`), `weekly` (list of `week`, `clicks`).

- [ ] **Step 1: Write the failing test (add to `tracking/tests.py`)**

```python
    def test_dashboard_shows_stats(self):
        User = get_user_model()
        user = User.objects.create_user("staff", password="x", is_staff=True)
        self.client.force_login(user)
        self.client.get("/go/internship-a/?utm_source=instagram")
        self.client.get("/track/view/internship-a/")
        response = self.client.get("/analytics/")
        self.assertContains(response, "Total clicks")
        self.assertContains(response, "1")
```

- [ ] **Step 2: Run to verify it fails**

Run: `python manage.py test tracking.tests.TrackingTests.test_dashboard_shows_stats -v 2`
Expected: FAIL — `tracking.views.dashboard` doesn't exist.

- [ ] **Step 3: Write the view**

```python
# tracking/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.shortcuts import render

from .models import ClickEvent, PageView, Unlock


@staff_member_required
def dashboard(request):
    views_by_title = {
        row["opportunity__title"]: row["views"]
        for row in PageView.objects.values("opportunity__title").annotate(views=Count("id"))
    }
    per_post = []
    for row in (
        ClickEvent.objects.values("opportunity__title")
        .annotate(clicks=Count("id"))
        .order_by("-clicks")[:10]
    ):
        views = views_by_title.get(row["opportunity__title"], 0)
        per_post.append(
            {
                "title": row["opportunity__title"],
                "clicks": row["clicks"],
                "views": views,
                "ctr": round(row["clicks"] / views, 3) if views else 0,
            }
        )

    per_category = [
        {"name": row["opportunity__category"], "clicks": row["clicks"]}
        for row in ClickEvent.objects.values("opportunity__category").annotate(clicks=Count("id"))
    ]
    by_source = [
        {"source": row["utm_source"], "clicks": row["clicks"]}
        for row in ClickEvent.objects.values("utm_source").annotate(clicks=Count("id"))
    ]
    weekly = [
        {"week": row["week"].strftime("%Y-%m-%d"), "clicks": row["clicks"]}
        for row in ClickEvent.objects.annotate(week=TruncWeek("timestamp"))
        .values("week")
        .annotate(clicks=Count("id"))
        .order_by("week")
    ]
    totals = {
        "clicks": ClickEvent.objects.count(),
        "views": PageView.objects.count(),
        "unlocks": Unlock.objects.count(),
    }
    totals["ctr"] = round(totals["clicks"] / totals["views"], 3) if totals["views"] else 0

    return render(
        request,
        "tracking/dashboard.html",
        {
            "totals": totals,
            "per_post": per_post,
            "per_category": per_category,
            "by_source": by_source,
            "weekly": weekly,
        },
    )
```

- [ ] **Step 4: Write the template**

```html
<!-- tracking/templates/tracking/dashboard.html -->
{% extends "base.html" %}

{% block title %}Analytics · NamoLead{% endblock %}

{% block content %}
<h1 class="text-2xl font-bold mb-6">Analytics</h1>

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
  <div class="bg-white border rounded-lg p-4"><div class="text-sm text-gray-500">Total clicks</div><div class="text-2xl font-bold">{{ totals.clicks }}</div></div>
  <div class="bg-white border rounded-lg p-4"><div class="text-sm text-gray-500">Page views</div><div class="text-2xl font-bold">{{ totals.views }}</div></div>
  <div class="bg-white border rounded-lg p-4"><div class="text-sm text-gray-500">Unlocks</div><div class="text-2xl font-bold">{{ totals.unlocks }}</div></div>
  <div class="bg-white border rounded-lg p-4"><div class="text-sm text-gray-500">View→click CTR</div><div class="text-2xl font-bold">{{ totals.ctr }}</div></div>
</div>

<div class="grid md:grid-cols-2 gap-6">
  <div class="bg-white border rounded-lg p-4">
    <h2 class="font-semibold mb-2">Clicks per post</h2>
    <canvas id="postChart"></canvas>
  </div>
  <div class="bg-white border rounded-lg p-4">
    <h2 class="font-semibold mb-2">Traffic source</h2>
    <canvas id="sourceChart"></canvas>
  </div>
  <div class="bg-white border rounded-lg p-4 md:col-span-2">
    <h2 class="font-semibold mb-2">Clicks per week</h2>
    <canvas id="weeklyChart"></canvas>
  </div>
</div>

<h2 class="text-lg font-semibold mt-8 mb-2">Per-post breakdown</h2>
<table class="w-full bg-white border rounded-lg text-sm">
  <thead><tr class="text-left border-b"><th class="p-2">Post</th><th class="p-2">Clicks</th><th class="p-2">Views</th><th class="p-2">CTR</th></tr></thead>
  <tbody>
  {% for p in per_post %}
    <tr class="border-b"><td class="p-2">{{ p.title }}</td><td class="p-2">{{ p.clicks }}</td><td class="p-2">{{ p.views }}</td><td class="p-2">{{ p.ctr }}</td></tr>
  {% empty %}
    <tr><td class="p-2" colspan="4">No clicks yet.</td></tr>
  {% endfor %}
  </tbody>
</table>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{{ per_post|json_script:"per-post" }}
{{ by_source|json_script:"by-source" }}
{{ weekly|json_script:"weekly" }}
<script>
const perPost = JSON.parse(document.getElementById('per-post').textContent);
const bySource = JSON.parse(document.getElementById('by-source').textContent);
const weekly = JSON.parse(document.getElementById('weekly').textContent);
new Chart(document.getElementById('postChart'), {
  type: 'bar',
  data: { labels: perPost.map(p => p.title), datasets: [{ label: 'Clicks', data: perPost.map(p => p.clicks) }] }
});
new Chart(document.getElementById('sourceChart'), {
  type: 'pie',
  data: { labels: bySource.map(s => s.source), datasets: [{ data: bySource.map(s => s.clicks) }] }
});
new Chart(document.getElementById('weeklyChart'), {
  type: 'line',
  data: { labels: weekly.map(w => w.week), datasets: [{ label: 'Clicks', data: weekly.map(w => w.clicks) }] }
});
</script>
{% endblock %}
```

- [ ] **Step 5: Run tests, verify pass**

```bash
python manage.py test -v 2
# expected: 11 passed
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: staff-only analytics dashboard with Chart.js"
```

---

### Task 5: Deployment artifacts + README

**Files:**
- Create: `Dockerfile`, `docker-compose.yml`, `README.md`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "namolead.wsgi", "--bind", "0.0.0.0:8000"]
```

- [ ] **Step 2: Write docker-compose.yml**

```yaml
services:
  web:
    build: .
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - static:/app/staticfiles
      - media:/app/media
    depends_on:
      - db
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: namolead
      POSTGRES_USER: namolead
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata: {}
  static: {}
  media: {}
```

- [ ] **Step 3: Write README.md**

```markdown
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

Production env vars (see .env.example): DJANGO_SECRET_KEY, DEBUG=False,
ALLOWED_HOSTS, IP_HASH_SALT, DATABASE_URL (Postgres), POSTGRES_PASSWORD.
Media files live on the `media` volume; swap to R2 via django-storages when the
site grows. HTTPS via Caddy/certbot or the platform's TLS terminator.
```

- [ ] **Step 4: Verify**

```bash
python manage.py check --deploy 2>&1 | grep -v "WARNING" ; python manage.py collectstatic --noinput
# no errors; staticfiles/ populated
docker compose config > /dev/null   # if docker installed; skip otherwise
```

- [ ] **Step 5: Final full check + commit**

```bash
python manage.py test -v 2
python manage.py seed_demo
python manage.py runserver 2>/dev/null & sleep 3; curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/; curl -s -o /dev/null -w "%{http_code}" -L http://127.0.0.1:8000/go/; kill %1
# expected: 200 404
```

```bash
git add -A
git commit -m "chore: docker deployment artifacts and README"
```

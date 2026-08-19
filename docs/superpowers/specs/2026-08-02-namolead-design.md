# NamoLead Opportunities Platform — MVP Design

**Date:** 2026-08-02
**Status:** Approved

## Goal

Replace the WhatsApp-only funnel with a searchable, SEO-indexed website where
NamoLead publishes career opportunities (image + paragraph + apply link) that
non-technical editors manage via Wagtail admin. Outbound clicks and page views
are tracked first-class (no analytics SaaS). Exclusive posts are gated behind
an Instagram-follow soft gate that mirrors the current "DM [KEYWORD]" mechanic.
Staff get a Chart.js analytics dashboard with view-to-click conversion.

## Decisions

- **Frontend:** server-rendered Wagtail templates + Tailwind (CDN). One
  codebase, cheapest to deploy, SEO native. Headless Next.js can be added
  later without model changes.
- **Structure:** two Django apps.
  - `opportunities` — CMS content (Wagtail Page subclasses), public templates,
    user-facing views (go-redirect, pageview beacon, gate unlock).
  - `tracking` — event models (ClickEvent, PageView, Unlock), IP-hashing util,
    staff-only analytics dashboard.
  - Rationale: CMS is read-mostly, tracking is write-mostly; they scale and
    migrate independently. Cross-app FKs use string references to avoid import
    cycles.
- **Post model:** plain fields only, no StreamField. A post is exactly
  featured image + short description + apply URL, plus category, organization,
  is_exclusive. Add StreamField blocks later if posts get richer.
- **Exclusivity:** soft gate, not access control. Unlock = follow
  @namolead on Instagram (self-asserted) + email capture. No OAuth, no
  accounts. Session flag unlocks the apply button for the visitor.
- **Dropped for MVP:** deadlines/countdowns, auto-archiving, Django-Q2/Redis,
  DRF API views, WhatsApp bot endpoint, R2 object storage, eligibility
  filtering. None have users yet; each is a one-line upgrade later.

## Data model

### opportunities.OpportunityIndexPage (Page)
- `max_count = 1`, hosts OpportunityPage children, serves at `/`.
- `get_context`: lists live children ordered by `-first_published_at`,
  filters by `?category=` (validated against choices).

### opportunities.OpportunityPage (Page)
- `category` — TextChoices: internship, simulation, govt-defense, scholarship,
  hackathon, certification.
- `organization` — CharField, blank.
- `short_description` — TextField (the paragraph).
- `featured_image` — FK to wagtailimages.Image, null/blank.
- `apply_url` — URLField (never linked directly; always via `/go/<slug>/`).
- `is_exclusive` — BooleanField; gates the apply button behind the soft gate.
- `get_context`: adds `unlocked` from session flag `unlocked_<pk>`.
- Wagtail gives slug, scheduled publishing, revisions, search for free.

### tracking.ClickEvent
opportunity FK (SET_NULL), timestamp (auto, indexed), referrer (255),
user_agent (255), hashed_ip (sha256), utm_source (validated:
whatsapp/instagram/direct, default direct).

### tracking.PageView
opportunity FK, timestamp (auto, indexed), hashed_ip.

### tracking.Unlock
opportunity FK, email, hashed_ip, timestamp (auto). One row per unlock
submission; no dedup constraint (analytics can count).

## Flows

1. **Detail page** renders image, paragraph, 1×1 beacon `<img>` hitting
   `/track/view/<slug>/` (logs PageView).
2. **Apply** — button links to `/go/<slug>/` (optionally
   `?utm_source=whatsapp|instagram|direct`). The view validates the source,
   logs ClickEvent (referrer, user_agent, hashed IP, source), 302s to the
   real apply_url. Unknown slug → 404.
3. **Gate** — exclusive post shows the gate panel instead of the button:
   follow link + email form posting to `/unlock/<slug>/`. Email validated
   with Django's validate_email; on success: Unlock row, session flag set,
   redirect back with success message. Invalid email → error message, no row.
4. **Analytics** — `/analytics/`, `staff_member_required` (reuses Wagtail
   admin login via LOGIN_URL). Cards for totals + CTR; charts: clicks per
   post (bar), traffic source (pie), clicks per week (line, TruncWeek); table
   with per-post clicks/views/CTR. Chart.js from CDN, data via `json_script`.

## Privacy & security

- Raw IPs are never stored — `sha256(IP_HASH_SALT + ":" + ip)` only.
- Outbound links only ever route through `/go/<slug>/`.
- Analytics is staff-only; Wagtail admin is the only editor surface.

## Ops

- Dev: SQLite (`env.db()` fallback), `runserver`, no `.env` needed.
- Prod: Postgres via `DATABASE_URL`, whitenoise for static, Dockerfile +
  docker-compose (web + postgres). Deploys to EC2 free tier or Railway.
- Seed command `seed_demo` (idempotent): root index at `/`, two demo posts
  (one exclusive), sets Site.root_page.
- Requirements pinned: Django ~=5.2, Wagtail ~=6.4, django-environ,
  whitenoise, gunicorn.

## Verification

Django tests: index lists + category filter, detail render, go-redirect
logs + 302 + source validation + 404, pageview beacon, gate block → unlock →
reveal, invalid email rejected, analytics staff-only + stats render.
Total ~11 tests across the two apps.

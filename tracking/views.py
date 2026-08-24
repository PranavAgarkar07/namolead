import re
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncHour, TruncWeek
from django.shortcuts import render
from django.utils import timezone

from .models import ClickEvent, PageView


# ---------------------------------------------------------------------------
# UA Helpers
# ---------------------------------------------------------------------------

def _detect_device(ua: str) -> str:
    ua_lower = ua.lower()
    if "android" in ua_lower:
        return "Android"
    if any(x in ua_lower for x in ("iphone", "ipad", "ipod")):
        return "Apple iOS"
    if "macintosh" in ua_lower or "mac os" in ua_lower:
        return "macOS"
    if "windows" in ua_lower:
        return "Windows"
    if "linux" in ua_lower:
        return "Linux"
    return "Other"


def _detect_browser(ua: str) -> str:
    ua_lower = ua.lower()
    if "edg/" in ua_lower:
        return "Edge"
    if "opr/" in ua_lower or "opera" in ua_lower:
        return "Opera"
    if "chrome" in ua_lower and "chromium" not in ua_lower:
        return "Chrome"
    if "firefox" in ua_lower:
        return "Firefox"
    if "safari" in ua_lower and "chrome" not in ua_lower:
        return "Safari"
    if "samsung" in ua_lower:
        return "Samsung"
    return "Other"


# ---------------------------------------------------------------------------
# Dashboard View
# ---------------------------------------------------------------------------

@staff_member_required
def dashboard(request):
    # --- Time-range filtering ---
    current_range = request.GET.get("range", "all")
    now = timezone.now()
    range_map = {
        "today": now.replace(hour=0, minute=0, second=0, microsecond=0),
        "7d":    now - timedelta(days=7),
        "30d":   now - timedelta(days=30),
    }
    since = range_map.get(current_range)

    clicks_qs = ClickEvent.objects.all()
    views_qs  = PageView.objects.all()
    if since:
        clicks_qs = clicks_qs.filter(timestamp__gte=since)
        views_qs  = views_qs.filter(timestamp__gte=since)

    # --- Per-post breakdown ---
    views_by_title = {
        row["opportunity__title"]: row["views"]
        for row in views_qs.values("opportunity__title").annotate(views=Count("id"))
    }
    per_post = []
    for row in (
        clicks_qs
        .values("opportunity__title", "opportunity__category")
        .annotate(clicks=Count("id"))
        .order_by("-clicks")[:10]
    ):
        views = views_by_title.get(row["opportunity__title"], 0)
        per_post.append({
            "title":    row["opportunity__title"] or "—",
            "category": row["opportunity__category"] or "",
            "clicks":   row["clicks"],
            "views":    views,
            "ctr":      round(row["clicks"] / views, 3) if views else 0,
        })

    # --- Category & source breakdown ---
    per_category = [
        {"name": row["opportunity__category"], "clicks": row["clicks"]}
        for row in clicks_qs.values("opportunity__category").annotate(clicks=Count("id"))
    ]
    by_source = [
        {"source": row["utm_source"], "clicks": row["clicks"]}
        for row in clicks_qs.values("utm_source").annotate(clicks=Count("id"))
    ]

    # --- Weekly trend ---
    weekly = [
        {"week": row["week"].strftime("%Y-%m-%d"), "clicks": row["clicks"]}
        for row in (
            clicks_qs
            .annotate(week=TruncWeek("timestamp"))
            .values("week")
            .annotate(clicks=Count("id"))
            .order_by("week")
        )
    ]

    # --- Hourly distribution (24 h) ---
    hour_map = {h: 0 for h in range(24)}
    for row in (
        clicks_qs
        .annotate(hr=TruncHour("timestamp"))
        .values("hr")
        .annotate(clicks=Count("id"))
    ):
        if row["hr"]:
            local_hr = timezone.localtime(row["hr"]).hour
            hour_map[local_hr] = hour_map.get(local_hr, 0) + row["clicks"]
    hourly = [{"hour": f"{h:02d}:00", "clicks": hour_map[h]} for h in range(24)]

    # --- Device & browser breakdown (from UA strings) ---
    device_counter: dict = {}
    browser_counter: dict = {}
    for ua in clicks_qs.values_list("user_agent", flat=True):
        dev  = _detect_device(ua)
        brw  = _detect_browser(ua)
        device_counter[dev]   = device_counter.get(dev, 0) + 1
        browser_counter[brw]  = browser_counter.get(brw, 0) + 1

    by_device  = [{"device": k, "count": v} for k, v in sorted(device_counter.items(),  key=lambda x: -x[1])]
    by_browser = [{"browser": k, "count": v} for k, v in sorted(browser_counter.items(), key=lambda x: -x[1])]

    # --- Unique visitors (distinct hashed IPs) ---
    unique_visitors = clicks_qs.exclude(hashed_ip="").values("hashed_ip").distinct().count()

    # --- Top source & category ---
    top_source_row = max(by_source,     key=lambda x: x["clicks"], default=None)
    top_cat_row    = max(per_category,  key=lambda x: x["clicks"], default=None)

    # --- Recent live feed (last 20 clicks) ---
    recent_events = []
    for ev in clicks_qs.select_related("opportunity").order_by("-timestamp")[:20]:
        recent_events.append({
            "title":     ev.opportunity.title if ev.opportunity else "—",
            "source":    ev.utm_source,
            "device":    _detect_device(ev.user_agent),
            "browser":   _detect_browser(ev.user_agent),
            "timestamp": ev.timestamp,
        })

    # --- Totals ---
    total_clicks = clicks_qs.count()
    total_views  = views_qs.count()
    totals = {
        "clicks":          total_clicks,
        "views":           total_views,
        "ctr":             round(total_clicks / total_views, 3) if total_views else 0,
        "unique_visitors": unique_visitors,
        "top_source":      (top_source_row["source"] or "direct").capitalize() if top_source_row else "—",
        "top_category":    (top_cat_row["name"] or "").replace("-", " ").title() if top_cat_row else "—",
    }

    return render(
        request,
        "tracking/dashboard.html",
        {
            "totals":        totals,
            "per_post":      per_post,
            "per_category":  per_category,
            "by_source":     by_source,
            "weekly":        weekly,
            "hourly":        hourly,
            "by_device":     by_device,
            "by_browser":    by_browser,
            "recent_events": recent_events,
            "current_range": current_range,
        },
    )

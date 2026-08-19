from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.shortcuts import render

from .models import ClickEvent, PageView


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

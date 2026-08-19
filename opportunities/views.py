from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string

from .models import Category, OpportunityPage

VALID_SOURCES = {"whatsapp", "instagram", "direct"}

SEARCH_LIMIT = 12


def search_posts(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    qs = OpportunityPage.objects.live()
    if category in Category.values:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(organization__icontains=q)
            | Q(short_description__icontains=q)
            | Q(body__icontains=q)
        )
    else:
        qs = qs.none()
    results = qs.order_by("-first_published_at")[:SEARCH_LIMIT]
    html = "".join(
        render_to_string("components/card.html", {"post": p, "request": request}, request=request)
        for p in results
    )
    return JsonResponse({"query": q, "count": len(results), "html": html})


def go_redirect(request, slug):
    page = OpportunityPage.objects.live().filter(slug=slug).first()
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
    page = OpportunityPage.objects.live().filter(slug=slug).first()
    if page is not None:
        from tracking.models import PageView
        from tracking.utils import hash_ip

        PageView.objects.create(opportunity=page, hashed_ip=hash_ip(request))
    return HttpResponse(status=200)
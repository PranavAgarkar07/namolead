from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from .models import OpportunityPage

VALID_SOURCES = {"whatsapp", "instagram", "direct"}


def go_redirect(request, slug):
    page = OpportunityPage.objects.live().filter(slug=slug).first()
    if page is None:
        raise Http404
    if page.is_exclusive and not request.session.get(f"unlocked_{page.pk}"):
        return redirect(page.get_url(request))
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

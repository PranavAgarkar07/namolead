from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

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

    ip_key = hash_ip(request)
    too_many = Unlock.objects.filter(
        hashed_ip=ip_key, timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count() >= settings.UNLOCK_RATE_LIMIT
    if too_many:
        messages.error(request, "Too many unlock requests from this device — try again later.")
        return redirect(page.get_url(request))

    token = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(minutes=settings.UNLOCK_LINK_TTL_MINUTES)
    unlock = Unlock.objects.create(
        opportunity=page,
        email=email,
        hashed_ip=ip_key,
        token=token,
        expires_at=expires_at,
    )

    verify_url = request.build_absolute_uri(
        reverse("opportunities:verify", kwargs={"token": token})
    )
    apply_url = request.build_absolute_uri(
        reverse("opportunities:go", kwargs={"slug": page.slug}) + "?utm_source=email"
    )
    subject = f"Your exclusive NamoLead unlock — {page.title}"
    message = (
        f"Hi,\n\nTo unlock \"{page.title}\" on NamoLead:\n\n"
        f"1. Confirm it's you: {verify_url}\n"
        f"2. Apply directly: {apply_url}\n\n"
        f"The 1 click link expires in {settings.UNLOCK_LINK_TTL_MINUTES} minutes.\n\n"
        f"Follow @namoleads on Instagram for more.\n— NamoLead"
    )
    sent = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
    if not sent:
        unlock.delete()
        messages.error(request, "Email send failed — try again shortly.")
        return redirect(page.get_url(request))
    return render(request, "opportunities/unlock_email_sent.html", {"page": page, "to_email": email})


def verify(request, token):
    from tracking.models import Unlock

    unlock = Unlock.objects.filter(token=token).first()
    valid = (
        unlock is not None
        and unlock.status == Unlock.Status.PENDING
        and unlock.expires_at
        and unlock.expires_at >= timezone.now()
    )
    if not valid:
        messages.error(request, "That verification link is invalid or has expired.")
        return redirect("/")
    unlock.status = Unlock.Status.VERIFIED
    unlock.save(update_fields=["status"])
    if unlock.opportunity_id:
        request.session[f"unlocked_{unlock.opportunity_id}"] = True
        return HttpResponseRedirect(unlock.opportunity.get_url(request))
    return HttpResponseRedirect("/")

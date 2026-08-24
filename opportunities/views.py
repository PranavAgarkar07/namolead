from datetime import timedelta
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Category, OpportunityPage

VALID_SOURCES = {"whatsapp", "instagram", "direct"}

SEARCH_LIMIT = 12


def search_posts(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    all_requested = request.GET.get("all", "").strip()
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
    elif not category and not all_requested:
        qs = qs.none()

    results = qs.order_by("-first_published_at")[:SEARCH_LIMIT]
    html = "".join(
        f"<div>{render_to_string('components/card.html', {'post': p, 'request': request}, request=request)}</div>"
        for p in results
    )
    return JsonResponse({
        "query": q,
        "category": category,
        "count": len(results),
        "html": html,
    })



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


def opportunities_list_view(request):
    category = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()
    qs = OpportunityPage.objects.live()
    if category in Category.values:
        qs = qs.filter(category=category)
    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(organization__icontains=query)
            | Q(short_description__icontains=query)
            | Q(body__icontains=query)
        )

    all_live = OpportunityPage.objects.live()
    week_ago = timezone.now() - timedelta(days=7)
    base = request.build_absolute_uri("/")

    ctx = {
        "opportunities": qs.order_by("-first_published_at"),
        "query": query,
        "result_count": qs.count() if query else 0,
        "total_count": all_live.count(),
        "categories": Category.choices,
        "active_category": category,
        "ticker_items": all_live.order_by("-first_published_at")[:8],
        "stats": {
            "live": all_live.count(),
            "categories": len(Category.choices),
            "this_week": all_live.filter(first_published_at__gte=week_ago).count(),
        },
        "breadcrumbs": [
            {"title": "Home", "url": base},
            {"title": "Opportunities", "url": ""},
        ],
    }
    return render(request, "pages/opportunities.html", ctx)


def about_view(request):
    base = request.build_absolute_uri("/")
    ctx = {
        "breadcrumbs": [
            {"title": "Home", "url": base},
            {"title": "About & Aim", "url": ""},
        ],
        "stats": {
            "live": OpportunityPage.objects.live().count(),
            "categories": len(Category.choices),
        },
    }
    return render(request, "pages/about.html", ctx)


def team_view(request):
    from .models import TeamMember

    base = request.build_absolute_uri("/")

    # ── Try loading from database (Wagtail admin editable) ───────────────────
    db_members = TeamMember.objects.filter(is_active=True).order_by("sort_order", "id")
    use_db = db_members.exists()

    if use_db:
        # Pull structured data from DB
        def _member_dict(m):
            return {
                "name": m.name,
                "role": m.role,
                "department": m.department,
                "bio": m.bio,
                "quote": m.quote,
                "instagram_url": m.instagram_url.strip() if m.instagram_url else "",
                "linkedin_url": m.linkedin_url.strip() if m.linkedin_url else "",
                "github_url": m.github_url.strip() if m.github_url else "",
                "portfolio_url": m.portfolio_url.strip() if m.portfolio_url else "",
                "email": m.email.strip() if m.email else "",
                "photo_url": m.photo_url,
                "image": "",
                "tier": m.tier,
                "academic_year": m.academic_year,
                "tenure": f"Academic Year {m.academic_year}" if m.academic_year else "Academic Year 2026–27",
            }

        founders = [_member_dict(m) for m in db_members if m.tier == TeamMember.Tier.FOUNDER]
        heads = [_member_dict(m) for m in db_members if m.tier == TeamMember.Tier.HEAD]
        executives = [_member_dict(m) for m in db_members if m.tier == TeamMember.Tier.EXECUTIVE]

        founder = founders[0] if founders else None
        team_members = heads + executives

    else:
        # ── Hardcoded fallback (used until DB is populated) ──────────────────
        founder = {
            "name": "Namokar Raka",
            "role": "Founder & President",
            "tenure": "Academic Year 2026–27",
            "bio": "Student mentor and President of NamoLead. Leading the founding team to break the gatekeeping around student career opportunities in India.",
            "quote": "Talent is evenly distributed across colleges in India, but opportunity awareness was not. NamoLead exists to make discovery instant, transparent, and completely free for every student.",
            "image": "img/team/president_pranav.png",
            "photo_url": "",
            "instagram_url": "https://instagram.com/namoleads",
            "github_url": "",
            "linkedin_url": "",
            "portfolio_url": "",
            "email": "",
        }

        heads = [
            {"name": "Vice President", "role": "Vice President", "department": "Executive Board", "bio": "Driving community strategy, institutional alignment, and overall program execution across colleges.", "image": "img/team/vice_president.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "General Secretary", "role": "General Secretary", "department": "Secretariat", "bio": "Overseeing operational governance, inter-departmental synergy, and community administration.", "image": "img/team/general_secretary.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Joint General Secretary", "role": "Joint General Secretary", "department": "Secretariat", "bio": "Supporting administrative execution, member coordination, and institutional relations.", "image": "img/team/joint_general_secretary.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Technical Head", "role": "Technical Head", "department": "Engineering & Tech", "bio": "Leading technical infrastructure, platform developments, and telemetry search pipelines.", "image": "img/team/technical_head.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Creative & Design Head", "role": "Creative and Design Head", "department": "Design & Identity", "bio": "Directing visual branding, typography, carousels, and high-impact digital design systems.", "image": "img/team/creative_design_head.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Marketing & Social Media Head", "role": "Marketing and Social Media Head", "department": "Growth & Social", "bio": "Managing campaigns, social channels, engagement growth, and multi-platform digital reach.", "image": "img/team/marketing_social_media_head.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Event Management Head", "role": "Event Management Head", "department": "Events & Programs", "bio": "Organizing campus drives, workshops, hackathons, and online webinars for pan-India students.", "image": "img/team/event_management_head.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Outreach & Partnership Head", "role": "Outreach & Partnership Head", "department": "Partnerships", "bio": "Building strategic alliances with colleges, youth clubs, student bodies, and industry partners.", "image": "img/team/outreach_partnership_head.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "PR & Communications Head", "role": "Public Relations & Communications Head", "department": "Communications", "bio": "Guiding external communications, media relations, student announcements, and official press.", "image": "img/team/pr_communications_head.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Documentation Head", "role": "Documentation Head", "department": "Editorial & Records", "bio": "Documenting reports, archives, guidelines, opportunity listings, and official publications.", "image": "img/team/documentation_head.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Community & Membership Head", "role": "Community and Membership Head", "department": "Community", "bio": "Nurturing student onboarding, community membership health, peer engagement, and support.", "image": "img/team/community_membership_head.jpg", "photo_url": "", "instagram_url": ""},
        ]

        executives = [
            {"name": "Technical Operations Executive", "role": "Technical Operations Executive", "department": "Operations & Tech", "bio": "Supporting portal uptime, technical maintenance, feature testing, and release rollouts.", "image": "img/team/technical_ops_executive.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Outreach & Community Executive", "role": "Outreach & Community Executive", "department": "Outreach", "bio": "Connecting with student leaders, campus ambassadors, and college network groups.", "image": "img/team/outreach_community_executive.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Marketing & Branding Executive", "role": "Marketing & Branding Executive", "department": "Growth & Brand", "bio": "Executing social campaigns, banner distribution, storytelling, and student reach initiatives.", "image": "img/team/marketing_branding_executive.jpg", "photo_url": "", "instagram_url": ""},
            {"name": "Membership & Community Executive", "role": "Membership & Community Executive", "department": "Community", "bio": "Facilitating membership queries, peer study circles, and community event participation.", "image": "img/team/membership_community_executive.jpg", "photo_url": "", "instagram_url": ""},
        ]

        team_members = heads + executives

    ctx = {
        "founder": founder,
        "heads": heads,
        "executives": executives,
        "team_members": team_members,
        "breadcrumbs": [
            {"title": "Home", "url": base},
            {"title": "Founding Team (2026–27)", "url": ""},
        ],
    }
    return render(request, "pages/team.html", ctx)



def events_view(request):
    base = request.build_absolute_uri("/")
    ctx = {
        "events": [],
        "breadcrumbs": [
            {"title": "Home", "url": base},
            {"title": "Events & Workshops", "url": ""},
        ],
    }
    return render(request, "pages/events.html", ctx)
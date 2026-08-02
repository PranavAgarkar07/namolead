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
        radar = OpportunityPage.objects.child_of(self).live()
        if category in Category.values:
            radar = radar.filter(category=category)
        ctx["radar"] = radar.order_by("-first_published_at")[:3]
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

from django.db import models
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page, Orderable
from wagtail.search import index
from wagtail.snippets.models import register_snippet


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
        all_live = OpportunityPage.objects.child_of(self).live().order_by("-first_published_at")
        week_ago = timezone.now() - timedelta(days=7)

        # Home page spotlights the latest 4 curated opportunities
        ctx["latest_opportunities"] = all_live[:4]
        ctx["opportunities"] = ctx["latest_opportunities"]
        ctx["radar"] = all_live[:3]
        ctx["ticker_items"] = all_live[:8]
        ctx["stats"] = {
            "live": all_live.count(),
            "categories": len(Category.choices),
            "this_week": all_live.filter(first_published_at__gte=week_ago).count(),
        }
        ctx["categories"] = Category.choices
        ctx["breadcrumbs"] = []
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
    body = RichTextField(
        blank=True,
        features=[
            "h2",
            "h3",
            "bold",
            "italic",
            "ol",
            "ul",
            "link",
            "document-link",
            "image",
            "embed",
            "hr",
        ],
        help_text="The full post. Headings, lists, links, inline images and embeds are supported.",
    )
    deadline = models.DateField(
        null=True,
        blank=True,
        help_text="Optional application deadline. The post stays listed but is tagged as missed after this date.",
    )
    featured_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Card image. Landscape fills the page top; vertical images sit left of the content.",
    )
    apply_url = models.URLField(help_text="Real destination URL. Visitors are routed via /go/<slug>/ for tracking.")

    content_panels = Page.content_panels + [
        FieldPanel("category"),
        FieldPanel("organization"),
        FieldPanel("featured_image"),
        FieldPanel("deadline"),
        FieldPanel("body"),
        InlinePanel("gallery_images", heading="More images", label="Image"),
        FieldPanel("short_description"),
        FieldPanel("apply_url"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("organization"),
        index.SearchField("short_description"),
        index.SearchField("body"),
    ]

    @property
    def is_portrait(self):
        return bool(
            self.featured_image
            and self.featured_image.height
            and self.featured_image.height > self.featured_image.width
        )

    @property
    def is_expired(self):
        return bool(self.deadline and self.deadline < timezone.localdate())

    def get_context(self, request, *args, **kwargs):
        ctx = super().get_context(request, *args, **kwargs)
        base = request.build_absolute_uri("/")
        ctx["breadcrumbs"] = [
            {"title": "Home", "url": base},
            {"title": "Opportunities", "url": base},
            {"title": self.get_category_display(), "url": f"{base}?category={self.category}"},
            {"title": self.title, "url": ""},
        ]
        return ctx


class OpportunityGalleryImage(Orderable):
    page = ParentalKey("opportunities.OpportunityPage", related_name="gallery_images")
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Image",
    )
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]


@register_snippet
class TeamMember(models.Model):
    """
    A team member managed via the Wagtail CMS snippets interface.
    Go to /cms/snippets/opportunities/teammember/ to add / edit / reorder.
    """

    class Tier(models.TextChoices):
        FOUNDER = "founder", "Founder / President"
        HEAD = "head", "Department Head"
        EXECUTIVE = "executive", "Operations Executive"

    # ── Core identity ───────────────────────────────────────────────────────
    name = models.CharField(
        max_length=128,
        help_text="Full name (e.g. Pranav Agarkar) or role title (e.g. Technical Head).",
    )
    role = models.CharField(
        max_length=128,
        help_text="Displayed designation label below the name.",
    )
    department = models.CharField(
        max_length=64,
        blank=True,
        help_text="Short department tag shown on the card (e.g. 'Engineering & Tech').",
    )
    tier = models.CharField(
        max_length=16,
        choices=Tier.choices,
        default=Tier.HEAD,
        help_text="Controls which section this member appears in on the team page.",
    )

    # ── Photo ────────────────────────────────────────────────────────────────
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Upload a portrait photo. Will be displayed as a circle crop — square or portrait images work best.",
    )

    # ── Bio ──────────────────────────────────────────────────────────────────
    bio = models.TextField(
        max_length=400,
        blank=True,
        help_text="Short one- or two-sentence description shown on the card.",
    )
    quote = models.TextField(
        max_length=500,
        blank=True,
        help_text="Optional pull-quote (displayed only on the Founder spotlight).",
    )

    # ── Social links ─────────────────────────────────────────────────────────
    instagram_url = models.URLField(
        blank=True,
        help_text="Instagram profile URL. Leave blank if none.",
    )
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn profile URL. Leave blank if none.")
    github_url = models.URLField(blank=True, help_text="GitHub profile URL. Leave blank if none (button will be hidden).")
    portfolio_url = models.URLField(blank=True, help_text="Personal website or portfolio URL. Leave blank if none.")
    email = models.EmailField(blank=True, help_text="Public contact email address. Leave blank if none.")

    # ── Display control ───────────────────────────────────────────────────────
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Lower numbers appear first within their tier section.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this member from the public team page without deleting.",
    )
    academic_year = models.CharField(
        max_length=16,
        default="2026–27",
        help_text="Academic year label (e.g. 2026–27).",
    )

    # ── Wagtail admin panels ─────────────────────────────────────────────────
    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("role"),
                FieldPanel("department"),
                FieldPanel("tier"),
                FieldPanel("academic_year"),
            ],
            heading="Identity",
        ),
        FieldPanel("photo"),
        MultiFieldPanel(
            [
                FieldPanel("bio"),
                FieldPanel("quote"),
            ],
            heading="Content",
        ),
        MultiFieldPanel(
            [
                FieldPanel("instagram_url"),
                FieldPanel("linkedin_url"),
                FieldPanel("github_url"),
                FieldPanel("portfolio_url"),
                FieldPanel("email"),
            ],
            heading="Social Links (Only filled links are displayed on the website)",
        ),
        MultiFieldPanel(
            [
                FieldPanel("sort_order"),
                FieldPanel("is_active"),
            ],
            heading="Display Settings",
        ),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return f"{self.name} — {self.role}"

    @property
    def photo_url(self):
        """Returns the URL of the photo, or an empty string if not set."""
        if self.photo:
            return self.photo.file.url
        return ""

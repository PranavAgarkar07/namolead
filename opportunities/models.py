from django.db import models
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Page, Orderable
from wagtail.search import index


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
        query = request.GET.get("q", "").strip()
        qs = OpportunityPage.objects.child_of(self).live()
        if category in Category.values:
            qs = qs.filter(category=category)
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(organization__icontains=query)
                | Q(short_description__icontains=query)
                | Q(body__icontains=query)
            )
        ctx["opportunities"] = qs.order_by("-first_published_at")
        ctx["query"] = query
        ctx["result_count"] = qs.count() if query else 0
        radar = qs
        ctx["radar"] = radar.order_by("-first_published_at")[:3]
        ctx["ticker_items"] = radar.order_by("-first_published_at")[:8]
        week_ago = timezone.now() - timedelta(days=7)
        ctx["stats"] = {
            "live": OpportunityPage.objects.child_of(self).live().count(),
            "categories": len(Category.choices),
            "this_week": OpportunityPage.objects.child_of(self)
            .live()
            .filter(first_published_at__gte=week_ago)
            .count(),
        }
        ctx["categories"] = Category.choices
        ctx["active_category"] = category
        base = request.build_absolute_uri("/")
        ctx["breadcrumbs"] = [
            {"title": "Home", "url": base},
            {"title": "Opportunities", "url": ""},
        ]
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

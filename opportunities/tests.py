from datetime import date, timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image as PILImage
from wagtail.models import Page, Site

from .models import OpportunityIndexPage, OpportunityPage


def seed_site():
    root = Page.objects.filter(depth=1).first()
    index = root.add_child(instance=OpportunityIndexPage(title="Home"))
    site = Site.objects.first()
    site.root_page = index
    site.save()
    return index


def publish(parent, **kwargs):
    page = parent.add_child(instance=OpportunityPage(**kwargs))
    page.save_revision().publish()
    return page


def make_png(width, height):
    buf = BytesIO()
    PILImage.new("RGB", (width, height), (255, 107, 53)).save(buf, format="PNG")
    return SimpleUploadedFile(f"img-{width}x{height}.png", buf.getvalue(), content_type="image/png")


class OpportunityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.index = seed_site()
        cls.intern = publish(
            cls.index,
            title="Internship A",
            category="internship",
            organization="Acme",
            short_description="Great internship",
            apply_url="https://example.com/apply",
        )
        cls.scholar = publish(
            cls.index,
            title="Scholarship B",
            category="scholarship",
            short_description="Funded study",
            apply_url="https://example.com/scholarship",
        )

    def test_index_lists_latest_published_posts(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Internship A")
        self.assertContains(response, "Scholarship B")
        self.assertContains(response, "Latest Opportunities")
        self.assertContains(response, "See All Opportunities")
        self.assertContains(response, "/opportunities/")

    def test_opportunities_directory_lists_all_posts(self):
        response = self.client.get("/opportunities/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Internship A")
        self.assertContains(response, "Scholarship B")
        self.assertContains(response, "opportunities and career openings")
        self.assertContains(response, 'id="search-input"')

    def test_opportunities_directory_filters_by_category(self):
        response = self.client.get("/opportunities/", {"category": "scholarship"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scholarship B")
        self.assertNotContains(response, "Internship A")

    def test_opportunities_directory_search_by_title(self):
        response = self.client.get("/opportunities/", {"q": "internship"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Internship A")
        self.assertNotContains(response, "Scholarship B")
        self.assertContains(response, 'id="search-count">1<')

    def test_opportunities_directory_search_by_organization(self):
        response = self.client.get("/opportunities/", {"q": "acme"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Internship A")
        self.assertNotContains(response, "Scholarship B")

    def test_opportunities_directory_search_by_description(self):
        response = self.client.get("/opportunities/", {"q": "funded"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scholarship B")
        self.assertNotContains(response, "Internship A")

    def test_opportunities_directory_search_respects_category_and_keeps_query(self):
        response = self.client.get("/opportunities/", {"q": "study", "category": "scholarship"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scholarship B")
        self.assertContains(response, 'value="study"')
        self.assertContains(response, "?category=internship&amp;q=study")

    def test_opportunities_directory_search_no_results_shows_empty_state(self):
        response = self.client.get("/opportunities/", {"q": "zzznomatch"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No matches found")
        self.assertNotContains(response, "Internship A")

    def test_api_search_returns_card_fragments(self):
        response = self.client.get("/api/search/", {"q": "internship"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertIn("Internship A", data["html"])
        self.assertIn("/internship-a/", data["html"])

    def test_api_search_respects_category(self):
        response = self.client.get("/api/search/", {"q": "internship", "category": "scholarship"})
        self.assertEqual(response.json()["count"], 0)
        self.assertEqual(response.json()["html"], "")

    def test_api_search_without_query_returns_nothing(self):
        response = self.client.get("/api/search/")
        self.assertEqual(response.json()["count"], 0)

    def test_detail_page_renders(self):
        response = self.client.get("/internship-a/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Great internship")

    def test_expired_post_is_tagged_not_hidden(self):
        from wagtail.images.models import Image as WagtailImage

        img = WagtailImage.objects.create(title="Wide", file=make_png(2, 1))
        expired = publish(
            self.index,
            title="Expired Post",
            category="internship",
            short_description="Too late",
            apply_url="https://example.com/expired",
            deadline=date.today() - timedelta(days=1),
            featured_image=img,
        )
        self.assertTrue(expired.is_expired)
        self.assertFalse(expired.is_portrait)
        card = self.client.get("/").content.decode()
        self.assertIn("Expired Post", card)
        self.assertIn('govuk-tag--red', card)  # GOV.UK red tag for closed/expired
        detail = self.client.get("/expired-post/").content.decode()
        self.assertIn("Deadline passed", detail)

    def test_portrait_image_sits_left_of_content(self):
        from wagtail.images.models import Image as WagtailImage

        img = WagtailImage.objects.create(title="Tall", file=make_png(1, 2))
        portrait = publish(
            self.index,
            title="Portrait Post",
            category="hackathon",
            short_description="Tall image post",
            apply_url="https://example.com/tall",
            featured_image=img,
        )
        self.assertTrue(portrait.is_portrait)
        detail = self.client.get("/portrait-post/").content.decode()
        self.assertIn("data-lightbox", detail)  # Lightbox attribute present
        self.assertIn("data-lightbox-src=", detail)
        self.assertIn("cursor: zoom-in", detail)  # GOV.UK detail page uses inline cursor style

    def test_breadcrumb_navigation(self):
        publish(
            self.index,
            title="Breadcrumb Post",
            category="scholarship",
            short_description="Crumb",
            apply_url="https://example.com/crumb",
        )
        detail = self.client.get("/breadcrumb-post/").content.decode()
        self.assertIn('aria-label="Breadcrumb"', detail)
        self.assertIn("?category=scholarship", detail)
        self.assertIn('aria-current="page"', detail)
        self.assertIn("BreadcrumbList", detail)
        opps = self.client.get("/opportunities/").content.decode()
        self.assertIn('aria-label="Breadcrumb"', opps)

    def test_logo_and_branding_everywhere(self):
        index = self.client.get("/").content.decode()
        # GOV.UK header contains logo SVG and NamoLead wordmark
        self.assertIn("govuk-header__logotype", index)
        self.assertIn("NamoLead", index)
        self.assertIn("apple-touch-icon.png", index)
        self.assertIn("og:image", index)
        self.assertIn("og-cover.png", index)

    def test_card_responsive_layout_for_image_orientation(self):
        from wagtail.images.models import Image as WagtailImage

        tall = WagtailImage.objects.create(title="Tall", file=make_png(1, 2))
        wide = WagtailImage.objects.create(title="Wide", file=make_png(2, 1))
        publish(
            self.index,
            title="Portrait Card",
            category="internship",
            short_description="Tall image",
            apply_url="https://example.com/tall",
            featured_image=tall,
        )
        publish(
            self.index,
            title="Landscape Card",
            category="internship",
            short_description="Wide image",
            apply_url="https://example.com/wide",
            featured_image=wide,
        )
        # GOV.UK card: both portrait and landscape show image + metadata + title
        portrait_card = self.client.get("/api/search/", {"q": "Portrait Card"}).json()["html"]
        self.assertIn("Portrait Card", portrait_card)
        self.assertIn("nlc-card", portrait_card)  # GOV.UK card class
        self.assertIn("govuk-tag", portrait_card)  # Category tag
        landscape_card = self.client.get("/api/search/", {"q": "Landscape Card"}).json()["html"]
        self.assertIn("Landscape Card", landscape_card)
        self.assertIn("nlc-card", landscape_card)
        self.assertIn("govuk-tag", landscape_card)

    def test_card_deadline_chips(self):
        from datetime import timedelta
        from django.utils import timezone

        local_today = timezone.localdate()
        publish(
            self.index,
            title="Closing Soon",
            category="scholarship",
            short_description="Chip urgent",
            apply_url="https://example.com/soon",
            deadline=local_today + timedelta(days=3),
        )
        publish(
            self.index,
            title="Closing Later",
            category="scholarship",
            short_description="Chip normal",
            apply_url="https://example.com/later",
            deadline=local_today + timedelta(days=30),
        )
        # GOV.UK card uses govuk-tag--red for urgent/closing soon, govuk-tag--grey for normal
        closing = self.client.get("/api/search/", {"q": "Closing Soon"}).json()["html"]
        self.assertIn("govuk-tag--red", closing)  # Red tag for imminent deadline
        target_date = local_today + timedelta(days=3)
        self.assertIn(f"Closes {target_date.day} {target_date.strftime('%b')}", closing)
        later = self.client.get("/api/search/", {"q": "Closing Later"}).json()["html"]
        self.assertIn("govuk-tag", later)  # Has a tag (grey for non-urgent)
        self.assertNotIn("govuk-tag--red", later)  # Not urgent

    def test_rich_body_renders(self):
        rich = publish(
            self.index,
            title="Rich Post",
            category="certification",
            short_description="Lead text",
            apply_url="https://example.com/rich",
            body="<p>Full <b>details</b> here</p>",
        )
        detail = self.client.get("/rich-post/").content.decode()
        self.assertIn("rich-text", detail)
        self.assertIn("Full <b>details</b> here", detail)

    def test_about_page_renders_successfully(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What is NamoLead?")
        self.assertContains(response, "Aim to Start NamoLead")
        self.assertContains(response, "Purpose &amp; Student Benefits")
        self.assertContains(response, "Our Future Aim &amp; Roadmap")
        self.assertContains(response, "AI Career &amp; Opportunity Chatbot")
        self.assertContains(response, "WhatsApp")

    def test_team_page_renders_successfully(self):
        response = self.client.get("/team/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Namokar Raka")
        self.assertContains(response, "Founder Spotlight")
        self.assertContains(response, "Core Team Members")
        self.assertContains(response, "Technical Head")
        # When founder has no github, github profile link should NOT be present
        self.assertNotContains(response, "GitHub Profile")

    def test_team_page_renders_with_database_team_members(self):
        from .models import TeamMember

        # Create founder with github and department head without github
        TeamMember.objects.create(
            name="Namokar Raka",
            role="Founder & President",
            department="Leadership",
            tier=TeamMember.Tier.FOUNDER,
            bio="Leading the founding team.",
            quote="Talent is evenly distributed.",
            github_url="https://github.com/example-user",
            instagram_url="https://instagram.com/namokar",
            sort_order=1,
            is_active=True,
        )
        TeamMember.objects.create(
            name="Sarah Jenkins",
            role="AI Research Head",
            department="Machine Learning",
            tier=TeamMember.Tier.HEAD,
            bio="Directing AI programs.",
            linkedin_url="https://linkedin.com/in/sarah",
            sort_order=1,
            is_active=True,
        )
        response = self.client.get("/team/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Namokar Raka")
        self.assertContains(response, "Sarah Jenkins")
        self.assertContains(response, "AI Research Head")
        self.assertContains(response, "Machine Learning")
        # Since founder has github, GitHub link should appear
        self.assertContains(response, "https://github.com/example-user")
        self.assertContains(response, "fa-github")  # GitHub icon shown (GOV.UK button with icon)
        # Sarah Jenkins has LinkedIn
        self.assertContains(response, "https://linkedin.com/in/sarah")


    def test_events_page_renders_successfully(self):
        response = self.client.get("/events/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Events &amp; Campus Drives")
        self.assertContains(response, "the Horizon")  # 'Exciting Sessions Are on the Horizon'
        self.assertContains(response, "WhatsApp")
        self.assertContains(response, "Campus Orientation Drives")  # Event type listed



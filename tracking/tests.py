from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.models import Page, Site

from opportunities.models import OpportunityIndexPage, OpportunityPage
from .models import ClickEvent, PageView, Unlock


def seed_site():
    root = Page.objects.filter(depth=1).first()
    index = root.add_child(instance=OpportunityIndexPage(title="Home"))
    site = Site.objects.first()
    site.root_page = index
    site.save()
    return index


class TrackingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        index = seed_site()
        cls.opp = index.add_child(
            instance=OpportunityPage(
                title="Internship A",
                category="internship",
                short_description="Great internship",
                apply_url="https://example.com/apply",
            )
        )
        cls.opp.save_revision().publish()
        cls.exclusive = index.add_child(
            instance=OpportunityPage(
                title="Exclusive C",
                category="internship",
                short_description="Secret",
                apply_url="https://example.com/secret",
                is_exclusive=True,
            )
        )
        cls.exclusive.save_revision().publish()

    def test_go_redirect_logs_click_and_302s(self):
        response = self.client.get("/go/internship-a/?utm_source=whatsapp")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://example.com/apply")
        self.assertEqual(ClickEvent.objects.count(), 1)
        self.assertEqual(ClickEvent.objects.first().utm_source, "whatsapp")

    def test_go_unknown_slug_404s(self):
        self.assertEqual(self.client.get("/go/nope/").status_code, 404)

    def test_invalid_source_falls_back_to_direct(self):
        self.client.get("/go/internship-a/?utm_source=spam")
        self.assertEqual(ClickEvent.objects.first().utm_source, "direct")

    def test_pageview_beacon_logs(self):
        response = self.client.get("/track/view/internship-a/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PageView.objects.count(), 1)

    def test_exclusive_gate_blocks_then_unlocks(self):
        response = self.client.get("/exclusive-c/")
        self.assertNotContains(response, "Apply now")
        self.assertContains(response, "Unlock")

        response = self.client.post("/unlock/exclusive-c/", {"email": "a@b.com"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Unlock.objects.filter(email="a@b.com").count(), 1)

        response = self.client.get("/exclusive-c/")
        self.assertContains(response, "Apply now")

    def test_invalid_email_rejected_no_unlock_created(self):
        self.client.post("/unlock/exclusive-c/", {"email": "not-an-email"})
        self.assertEqual(Unlock.objects.count(), 0)

    def test_analytics_requires_staff(self):
        self.assertEqual(self.client.get("/analytics/").status_code, 302)
        User = get_user_model()
        user = User.objects.create_user("staff", password="x", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get("/analytics/").status_code, 200)

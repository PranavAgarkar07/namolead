from django.contrib.auth import get_user_model
from django.core import mail
from django.test import RequestFactory, TestCase
from wagtail.models import Page, Site

from opportunities.models import OpportunityIndexPage, OpportunityPage
from .models import ClickEvent, PageView, Unlock
from .utils import hash_ip


def client_ip_key():
    req = RequestFactory().get("/")
    req.META["REMOTE_ADDR"] = "127.0.0.1"
    return hash_ip(req)


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

    def test_exclusive_gate_blocks_until_email_verified(self):
        response = self.client.get("/exclusive-c/")
        self.assertNotContains(response, "Apply now")
        self.assertContains(response, "Unlock")

        response = self.client.post("/unlock/exclusive-c/", {"email": "a@b.com"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email sent")
        unlocking = Unlock.objects.get(email="a@b.com")
        self.assertEqual(unlocking.status, Unlock.Status.PENDING)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"/verify/{unlocking.token}/", mail.outbox[0].body)
        self.assertIn("/go/exclusive-c/?utm_source=email", mail.outbox[0].body)

        response = self.client.get("/exclusive-c/")
        self.assertNotContains(response, "Apply now")

        response = self.client.get(f"/verify/{unlocking.token}/")
        self.assertEqual(response.status_code, 302)
        unlocking.refresh_from_db()
        self.assertEqual(unlocking.status, Unlock.Status.VERIFIED)

        response = self.client.get("/exclusive-c/")
        self.assertContains(response, "Apply now")

    def test_exclusive_go_redirect_enforces_gate_until_verified(self):
        response = self.client.get("/go/exclusive-c/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/exclusive-c/")
        self.assertEqual(ClickEvent.objects.count(), 0)

        self.client.post("/unlock/exclusive-c/", {"email": "a@b.com"})
        unlocking = Unlock.objects.get(email="a@b.com")
        self.client.get(f"/verify/{unlocking.token}/")

        response = self.client.get("/go/exclusive-c/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://example.com/secret")
        self.assertEqual(ClickEvent.objects.count(), 1)

    def test_invalid_token_rejected_and_gate_stays_locked(self):
        Unlock.objects.create(
            opportunity=self.exclusive,
            email="c@d.com",
            hashed_ip=client_ip_key(),
            token="singleuse",
            expires_at=None,
        )
        response = self.client.get(f"/verify/singleuse/")
        self.assertEqual(response.status_code, 302)
        unlocking = Unlock.objects.get(token="singleuse")
        self.assertEqual(unlocking.status, Unlock.Status.PENDING)
        response = self.client.get("/exclusive-c/")
        self.assertNotContains(response, "Apply now")

    def test_invalid_email_rejected_no_unlock_created(self):
        self.client.post("/unlock/exclusive-c/", {"email": "not-an-email"})
        self.assertEqual(Unlock.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_rate_limit_blocks_excess_requests(self):
        Unlock.objects.bulk_create(
            [
                Unlock(opportunity=self.exclusive, email=f"u{i}@b.com", hashed_ip=client_ip_key(), token=f"tok{i}", expires_at=None)
                for i in range(5)
            ]
        )
        response = self.client.post("/unlock/exclusive-c/", {"email": "over@b.com"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Unlock.objects.filter(email="over@b.com").exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_analytics_requires_staff(self):
        self.assertEqual(self.client.get("/analytics/").status_code, 302)
        User = get_user_model()
        user = User.objects.create_user("staff", password="x", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get("/analytics/").status_code, 200)

    def test_dashboard_shows_stats(self):
        User = get_user_model()
        user = User.objects.create_user("staff", password="x", is_staff=True)
        self.client.force_login(user)
        self.client.get("/go/internship-a/?utm_source=instagram")
        self.client.get("/track/view/internship-a/")
        response = self.client.get("/analytics/")
        self.assertContains(response, "Total clicks")
        self.assertContains(response, "1")

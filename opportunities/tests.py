from django.test import TestCase
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

    def test_index_lists_published_posts(self):
        response = self.client.get("/")
        self.assertContains(response, "Internship A")
        self.assertContains(response, "Scholarship B")

    def test_index_filters_by_category(self):
        response = self.client.get("/", {"category": "scholarship"})
        self.assertContains(response, "Scholarship B")
        self.assertNotContains(response, "Internship A")

    def test_detail_page_renders(self):
        response = self.client.get("/internship-a/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Great internship")

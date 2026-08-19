import environ
from django.core.management.base import BaseCommand
from wagtail.models import Page, Site

from opportunities.models import OpportunityIndexPage, OpportunityPage


class Command(BaseCommand):
    help = "Create the index page at / and two demo posts. Dev only; set SEED_DEMO=1."

    def handle(self, *args, **options):
        if not environ.Env().bool("SEED_DEMO", default=False):
            self.stdout.write("Skipped. Run with SEED_DEMO=1 (dev only).")
            return
        if OpportunityIndexPage.objects.exists():
            self.stdout.write("Already seeded.")
            return
        root = Page.objects.filter(depth=1).first()
        index = root.add_child(instance=OpportunityIndexPage(title="Home"))
        site = Site.objects.first()
        site.root_page = index
        site.save()

        demo = [
            dict(
                title="Google Summer of Code",
                category="internship",
                organization="Google",
                short_description="Paid remote internship writing open-source code. Apply before the deadline.",
                apply_url="https://summerofcode.withgoogle.com/",
            ),
            dict(
                title="Forage: JPMorgan Virtual Simulation",
                category="simulation",
                organization="Forage",
                short_description="Free 5-hour virtual job simulation.",
                apply_url="https://www.theforage.com/",
            ),
        ]
        for data in demo:
            page = index.add_child(instance=OpportunityPage(**data))
            page.save_revision().publish()

        self.stdout.write(self.style.SUCCESS("Seeded. Create an editor: python manage.py createsuperuser"))

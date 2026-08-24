from pathlib import Path
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from wagtail.images import get_image_model
from opportunities.models import TeamMember


class Command(BaseCommand):
    help = "Seeds all 16 NamoLead founding team members with Wagtail Images into the database."

    def handle(self, *args, **options):
        Image = get_image_model()
        team_img_dir = Path(settings.BASE_DIR) / "namolead" / "static" / "img" / "team"

        members_data = [
            # Founder / President
            {
                "name": "Namokar Raka",
                "role": "Founder & President",
                "department": "Leadership",
                "tier": TeamMember.Tier.FOUNDER,
                "academic_year": "2026–27",
                "bio": "Student mentor and President of NamoLead. Leading the founding team to break the gatekeeping around student career opportunities in India.",
                "quote": "Talent is evenly distributed across colleges in India, but opportunity awareness was not. NamoLead exists to make discovery instant, transparent, and completely free for every student.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "portfolio_url": "",
                "email": "",
                "image_file": "president_pranav.png",
                "sort_order": 1,
            },
            # Department Heads
            {
                "name": "Vice President",
                "role": "Vice President",
                "department": "Executive Board",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Driving community strategy, institutional alignment, and overall program execution across colleges.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "vice_president.png",
                "sort_order": 1,
            },
            {
                "name": "General Secretary",
                "role": "General Secretary",
                "department": "Secretariat",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Overseeing operational governance, inter-departmental synergy, and community administration.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "general_secretary.png",
                "sort_order": 2,
            },
            {
                "name": "Joint General Secretary",
                "role": "Joint General Secretary",
                "department": "Secretariat",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Supporting administrative execution, member coordination, and institutional relations.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "joint_general_secretary.png",
                "sort_order": 3,
            },
            {
                "name": "Technical Head",
                "role": "Technical Head",
                "department": "Engineering & Tech",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Leading technical infrastructure, platform developments, and telemetry search pipelines.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "technical_head.png",
                "sort_order": 4,
            },
            {
                "name": "Creative & Design Head",
                "role": "Creative and Design Head",
                "department": "Design & Identity",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Directing visual branding, typography, carousels, and high-impact digital design systems.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "creative_design_head.png",
                "sort_order": 5,
            },
            {
                "name": "Marketing & Social Media Head",
                "role": "Marketing and Social Media Head",
                "department": "Growth & Social",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Managing campaigns, social channels, engagement growth, and multi-platform digital reach.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "marketing_social_media_head.png",
                "sort_order": 6,
            },
            {
                "name": "Event Management Head",
                "role": "Event Management Head",
                "department": "Events & Programs",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Organizing campus drives, workshops, hackathons, and online webinars for pan-India students.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "event_management_head.png",
                "sort_order": 7,
            },
            {
                "name": "Outreach & Partnership Head",
                "role": "Outreach & Partnership Head",
                "department": "Partnerships",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Building strategic alliances with colleges, youth clubs, student bodies, and industry partners.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "outreach_partnership_head.png",
                "sort_order": 8,
            },
            {
                "name": "PR & Communications Head",
                "role": "Public Relations & Communications Head",
                "department": "Communications",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Guiding external communications, media relations, student announcements, and official press.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "pr_communications_head.png",
                "sort_order": 9,
            },
            {
                "name": "Documentation Head",
                "role": "Documentation Head",
                "department": "Editorial & Records",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Documenting reports, archives, guidelines, opportunity listings, and official publications.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "documentation_head.png",
                "sort_order": 10,
            },
            {
                "name": "Community & Membership Head",
                "role": "Community and Membership Head",
                "department": "Community",
                "tier": TeamMember.Tier.HEAD,
                "academic_year": "2026–27",
                "bio": "Nurturing student onboarding, community membership health, peer engagement, and support.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "community_membership_head.png",
                "sort_order": 11,
            },
            # Operations Executives
            {
                "name": "Technical Operations Executive",
                "role": "Technical Operations Executive",
                "department": "Operations & Tech",
                "tier": TeamMember.Tier.EXECUTIVE,
                "academic_year": "2026–27",
                "bio": "Supporting portal uptime, technical maintenance, feature testing, and release rollouts.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "technical_ops_executive.png",
                "sort_order": 1,
            },
            {
                "name": "Outreach & Community Executive",
                "role": "Outreach & Community Executive",
                "department": "Outreach",
                "tier": TeamMember.Tier.EXECUTIVE,
                "academic_year": "2026–27",
                "bio": "Connecting with student leaders, campus ambassadors, and college network groups.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "outreach_community_executive.png",
                "sort_order": 2,
            },
            {
                "name": "Marketing & Branding Executive",
                "role": "Marketing & Branding Executive",
                "department": "Growth & Brand",
                "tier": TeamMember.Tier.EXECUTIVE,
                "academic_year": "2026–27",
                "bio": "Executing social campaigns, banner distribution, storytelling, and student reach initiatives.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "marketing_branding_executive.png",
                "sort_order": 3,
            },
            {
                "name": "Membership & Community Executive",
                "role": "Membership & Community Executive",
                "department": "Community",
                "tier": TeamMember.Tier.EXECUTIVE,
                "academic_year": "2026–27",
                "bio": "Facilitating membership queries, peer study circles, and community event participation.",
                "instagram_url": "https://instagram.com/namoleads",
                "github_url": "",
                "linkedin_url": "",
                "image_file": "membership_community_executive.png",
                "sort_order": 4,
            },
        ]

        self.stdout.write(f"Seeding {len(members_data)} team members...")
        created_count = 0
        updated_count = 0

        for item in members_data:
            img_filename = item.pop("image_file")
            img_path = team_img_dir / img_filename

            wagtail_img = None
            if img_path.exists():
                title = f"{item['name']} - Portrait"
                existing_img = Image.objects.filter(title=title).first()
                if existing_img:
                    with open(img_path, "rb") as f:
                        existing_img.file.save(img_filename, File(f), save=True)
                    wagtail_img = existing_img
                    self.stdout.write(self.style.SUCCESS(f"  Updated Wagtail Image: {wagtail_img.title}"))
                else:
                    with open(img_path, "rb") as f:
                        wagtail_img = Image(title=title)
                        wagtail_img.file.save(img_filename, File(f), save=True)
                    self.stdout.write(self.style.SUCCESS(f"  Created Wagtail Image: {wagtail_img.title}"))

            member, created = TeamMember.objects.update_or_create(
                name=item["name"],
                role=item["role"],
                defaults={
                    **item,
                    "photo": wagtail_img,
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  [+] Created: {member.name} ({member.get_tier_display()})"))
            else:
                updated_count += 1
                self.stdout.write(self.style.NOTICE(f"  [*] Updated: {member.name} ({member.get_tier_display()})"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Seeded {created_count} new, updated {updated_count} team members into CMS Wagtail."
        ))


from django.db import models


class ClickEvent(models.Model):
    opportunity = models.ForeignKey(
        "opportunities.OpportunityPage", null=True, on_delete=models.SET_NULL, related_name="clicks"
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    referrer = models.CharField(max_length=255, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    hashed_ip = models.CharField(max_length=64, blank=True)
    utm_source = models.CharField(max_length=32, blank=True, default="direct")


class PageView(models.Model):
    opportunity = models.ForeignKey(
        "opportunities.OpportunityPage", null=True, on_delete=models.SET_NULL, related_name="views"
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    hashed_ip = models.CharField(max_length=64, blank=True)


class Unlock(models.Model):
    opportunity = models.ForeignKey(
        "opportunities.OpportunityPage", null=True, on_delete=models.SET_NULL, related_name="unlocks"
    )
    email = models.EmailField()
    hashed_ip = models.CharField(max_length=64, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

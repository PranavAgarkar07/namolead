from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def days_left(value):
    if not value:
        return None
    return (value - timezone.localdate()).days

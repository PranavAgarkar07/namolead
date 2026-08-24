from django.contrib import admin
from django.utils.html import format_html
from .models import TeamMember


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "department", "tier", "sort_order", "is_active", "academic_year", "photo_preview")
    list_filter = ("tier", "department", "is_active", "academic_year")
    search_fields = ("name", "role", "department", "bio")
    list_editable = ("sort_order", "is_active")
    ordering = ("tier", "sort_order", "id")

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="width:36px; height:36px; border-radius:50%; object-fit:cover; object-position:top;" />', obj.photo.file.url)
        return "-"
    photo_preview.short_description = "Photo"
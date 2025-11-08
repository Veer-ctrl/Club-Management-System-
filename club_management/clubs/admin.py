from django.contrib import admin
from .models import Club, Membership


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "contact_email")
    list_filter = ("is_active",)
    search_fields = ("name", "description", "contact_email")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "club", "role", "status", "join_date")
    list_filter = ("status", "role", "club")
    search_fields = ("user__username", "user__personal_email", "club__name")



from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ["username", "role", "branch", "status", "created_at"]
    list_filter   = ["role", "status", "branch"]
    search_fields = ["username", "phone"]
    ordering      = ["-created_at"]
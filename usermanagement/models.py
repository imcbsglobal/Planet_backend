from django.db import models
from master.models import Branch  # adjust import path if your branch model is elsewhere


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("Super Admin", "Super Admin"),
        ("Admin", "Admin"),
        ("User", "User"),
    ]
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]

    username   = models.CharField(max_length=150, unique=True)
    password   = models.CharField(max_length=255)          # store hashed via set_password
    address    = models.TextField(blank=True, default="")
    phone      = models.CharField(max_length=20, blank=True, default="")
    branch     = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default="User")
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Active")
    profile_photo = models.ImageField(upload_to="user_photos/", null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "usermanagement_userprofile"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} ({self.role})"
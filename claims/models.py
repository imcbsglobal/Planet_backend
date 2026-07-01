from django.conf import settings
from django.db import models


class Claim(models.Model):
    STATUS_CHOICES = [
        ("Claimed", "Claimed"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Pending", "Pending"),
    ]

    # Company is one of the fixed companies whose client_id maps to the
    # shared acc-master / acc-departments APIs (see COMPANY_CLIENT_IDS in the frontend)
    company = models.CharField(max_length=100)

    # department/client are codes coming from the external accmaster.imcbs.com
    # APIs (acc-departments / acc-master) — stored as plain strings/codes, not FKs,
    # since they live in an external system.
    department = models.CharField(max_length=50)          # department_id from acc-departments
    department_name = models.CharField(max_length=255, blank=True, default="")  # cached display name

    client = models.CharField(max_length=50)               # code from acc-master
    client_name = models.CharField(max_length=255, blank=True, default="")      # cached display name

    expense_type = models.CharField(max_length=64)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()

    receipt = models.FileField(upload_to="claims/receipts/%Y/%m/", null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Claimed")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claims",
    )
    created_by_name = models.CharField(max_length=150, blank=True, default="")  # denormalised from token

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Claim #{self.pk} - {self.client_name or self.client} ({self.status})"

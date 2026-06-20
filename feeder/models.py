from django.db import models


class Feeder(models.Model):
    STATUS_CHOICES = [
        ("Pending",         "Pending"),
        ("Accepted",        "Accepted"),
        ("Rejected",        "Rejected"),
        ("Key Uploaded",    "Key Uploaded"),
        ("Under Progress",  "Under Progress"),
    ]
    ADM_STATUS_CHOICES = [
        ("Pending",  "Pending"),
        ("Rejected", "Rejected"),
        ("Verified", "Verified"),
    ]

    # Primary Details
    name            = models.CharField(max_length=255)
    address         = models.CharField(max_length=500, blank=True, null=True)
    location        = models.CharField(max_length=255, blank=True, null=True)
    area            = models.CharField(max_length=255, blank=True, null=True)
    district        = models.CharField(max_length=255, blank=True, null=True)
    state           = models.CharField(max_length=255, blank=True, null=True)
    contact_person  = models.CharField(max_length=255, blank=True, null=True)
    phone           = models.CharField(max_length=20,  blank=True, null=True)
    email           = models.CharField(max_length=255, blank=True, null=True)
    reputed_name    = models.CharField(max_length=255, blank=True, null=True)
    reputed_phone   = models.CharField(max_length=20,  blank=True, null=True)

    # Client Details
    software        = models.CharField(max_length=255, blank=True, null=True)
    business_nature = models.CharField(max_length=255, blank=True, null=True)
    branch          = models.CharField(max_length=255, blank=True, null=True)
    no_of_system    = models.PositiveIntegerField(blank=True, null=True)
    pin_code        = models.CharField(max_length=10,  blank=True, null=True)
    country         = models.CharField(max_length=100, blank=True, null=True)
    install_date    = models.DateField(blank=True, null=True)
    remark          = models.TextField(blank=True, null=True)
    software_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_cost      = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Meta
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    adm_status      = models.CharField(max_length=20, choices=ADM_STATUS_CHOICES, default="Pending")
    created_by      = models.CharField(max_length=150, blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "feeder"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
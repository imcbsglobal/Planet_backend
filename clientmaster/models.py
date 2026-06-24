from django.db import models
from master.models import Branch, Corporate, District, State, Country, Software, BusinessNature, SP


class ClientMaster(models.Model):
    # Basic info
    code              = models.CharField(max_length=50, unique=True)
    status            = models.CharField(max_length=20, blank=True, default="")
    type              = models.CharField(max_length=30, blank=True, default="")
    branch            = models.ForeignKey(Branch,        on_delete=models.SET_NULL, null=True, blank=True, related_name="clientmaster_set")
    corporate         = models.ForeignKey(Corporate,     on_delete=models.SET_NULL, null=True, blank=True, related_name="clientmaster_set")

    # SUC / Service Charge conditional fields
    suc_amount        = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    suc_end_date      = models.DateField(null=True, blank=True)
    payment_class     = models.CharField(max_length=20, blank=True, default="")

    # Basic details
    name              = models.CharField(max_length=200)
    address           = models.TextField(blank=True, default="")
    location          = models.CharField(max_length=200, blank=True, default="")
    place             = models.CharField(max_length=200, blank=True, default="")
    pin_code          = models.CharField(max_length=10,  blank=True, default="")
    district          = models.ForeignKey(District,      on_delete=models.SET_NULL, null=True, blank=True, related_name="clientmaster_set")
    state             = models.ForeignKey(State,         on_delete=models.SET_NULL, null=True, blank=True, related_name="clientmaster_set")
    country           = models.ForeignKey(Country,       on_delete=models.SET_NULL, null=True, blank=True, related_name="clientmaster_set")

    # Contact
    person_name           = models.CharField(max_length=200, blank=True, default="")
    reputed_person_name   = models.CharField(max_length=200, blank=True, default="")
    phone1                = models.CharField(max_length=20,  blank=True, default="")
    phone2                = models.CharField(max_length=20,  blank=True, default="")
    phone3                = models.CharField(max_length=20,  blank=True, default="")
    reputed_person1       = models.CharField(max_length=20,  blank=True, default="")
    reputed_person2       = models.CharField(max_length=20,  blank=True, default="")
    email                 = models.EmailField(blank=True, default="")

    # Business details
    software          = models.ForeignKey(Software,      on_delete=models.SET_NULL, null=True, blank=True, related_name="clientmaster_set")
    business_nature   = models.ForeignKey(BusinessNature,on_delete=models.SET_NULL, null=True, blank=True, related_name="clientmaster_set")
    installation_date = models.DateField(null=True, blank=True)
    account_link      = models.CharField(max_length=500, blank=True, default="")

    # Licence details
    licence_type      = models.CharField(max_length=30,  blank=True, default="")
    no_of_seats       = models.PositiveIntegerField(null=True, blank=True)
    service_pack      = models.ForeignKey(SP,            on_delete=models.SET_NULL, null=True, blank=True, related_name="clientmaster_set")
    renewal_date      = models.DateField(null=True, blank=True)
    software_amount   = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    created_by        = models.CharField(max_length=150, blank=True, default="")
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clientmaster"
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} – {self.name}"

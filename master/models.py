from django.db import models


class BaseModel(models.Model):
    """Shared fields for all master models."""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} – {self.name}"


class Branch(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = "master_branch"


class Software(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = "master_software"


class BusinessNature(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = "master_business_nature"


class District(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = "master_district"


class State(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = "master_state"


class Country(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = "master_country"


class SP(BaseModel):
    class Meta(BaseModel.Meta):
        db_table = "master_sp"

from django.db import models


class Installation(models.Model):
    key         = models.CharField(max_length=50)          # feeder's unique_code
    feeder      = models.ForeignKey(
                    "feeder.Feeder",
                    on_delete=models.SET_NULL,
                    null=True, blank=True, related_name="installations"
                  )
    date        = models.DateField(null=True, blank=True)
    attachment  = models.FileField(upload_to="installation_keys/", null=True, blank=True)
    created_by  = models.CharField(max_length=150, blank=True, default="")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "installation"
        db_table  = "installation"
        ordering  = ["-created_at"]

    def __str__(self):
        return f"{self.key} — {self.feeder}"
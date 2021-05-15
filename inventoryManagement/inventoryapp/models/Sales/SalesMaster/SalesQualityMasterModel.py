from django.db import models
from django.utils import timezone


class SalesQualityMaster(models.Model):
    sales_quality_name = models.CharField(max_length=50)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Sales_Quality_Master'

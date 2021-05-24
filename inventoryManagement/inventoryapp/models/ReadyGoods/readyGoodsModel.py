from django.db import models
from django.utils import timezone
from inventoryapp.models.greyModel import *
from inventoryapp.models.Sales.SalesMaster.SalesQualityMasterModel import *

class LumpStock(models.Model):
    felt_book_number = models.CharField(primary_key=True,max_length=10)
    design_number = models.IntegerField(null=False, default = 0)

    from_felt_thans = models.IntegerField(null = False, default = 0)
    from_felt_tp = models.IntegerField(null = False, default = 0)
    from_felt_date = models.DateField(null=True, default=timezone.now)

    in_packing_thans = models.IntegerField(null = False, default = 0)
    in_packing_tp = models.IntegerField(null = False, default = 0)
    in_packing_date = models.DateField(null=True, default=timezone.now)

    grey_quality  = models.ForeignKey(GreyQualityMaster,blank=False,null=False,on_delete=models.PROTECT)
    sales_quality = models.ForeignKey(SalesQualityMaster,blank=False,null=False,on_delete=models.PROTECT)

    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)

    class Meta:
        db_table = 'Lump_Stock'

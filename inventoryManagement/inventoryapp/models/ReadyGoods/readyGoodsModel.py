from django.db import models
from django.utils import timezone
from inventoryapp.models.greyModel import *
from inventoryapp.models.Sales.SalesMaster.SalesQualityMasterModel import *

class ReadyLumpStock(models.Model):
    design_number = models.IntegerField(null=False, default = 0)
    felt_thans = models.IntegerField(null = False, default = 0)
    in_packing_thans = models.IntegerField(null = False, default = 0)
    grey_quality  = models.ForeignKey(GreyQualitiesMaster,blank=False,null=False,on_delete=models.PROTECT)
    sales_quality = models.ForeignKey(SalesQualityMaster,blank=False,null=False,on_delete=models.PROTECT)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)

    class Meta:
        db_table = 'Ready_Lump_Stock'

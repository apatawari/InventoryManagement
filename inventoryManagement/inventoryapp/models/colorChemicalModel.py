from django.db import models
from django.utils import timezone


######################################       COLOR      ##########################################
class ColorAndChemicalsSupplier(models.Model):
    supplier = models.CharField(max_length=50)
    address = models.CharField(null=True,max_length=100)
    city = models.CharField(null=True,max_length=20)

    class Meta:
        db_table = 'Chemicals_Supplier_master'

class Color(models.Model):
    color = models.CharField(max_length=50)
    quantity = models.FloatField(max_length=15,default=0.0)

    class Meta:
        db_table = 'Chemicals_master'

class ChemicalsGodownsMaster(models.Model):
    godown = models.CharField(max_length=50)

    class Meta:
        db_table = 'Chemicals_Godown_master'

class ChemicalsLooseGodownMaster(models.Model):
    lease = models.CharField(max_length=50)

    class Meta:
        db_table = 'Chemicals_Loose_Godown_master'

class ChemicalsUnitsMaster(models.Model):
    unit = models.CharField(max_length=50)

    class Meta:
        db_table = 'Units_master'

class ColorRecord(models.Model):
    color = models.ForeignKey(Color,blank=True,null=True,on_delete=models.PROTECT)
    supplier = models.ForeignKey(ColorAndChemicalsSupplier,blank=True,null=True,on_delete=models.PROTECT)
    order_date = models.DateField(default=None)
    order_no = models.IntegerField()
    quantity = models.FloatField()
    unit = models.ForeignKey(ChemicalsUnitsMaster,blank=True,null=True,on_delete=models.PROTECT)
    rate = models.FloatField()
    amount = models.FloatField(max_length=15)
    state = models.CharField(max_length=50)
    recieving_date = models.DateField(null=True,default=None)
    total_quantity = models.FloatField()
    godown = models.ForeignKey(ChemicalsGodownsMaster,blank=True,null=True,on_delete=models.PROTECT)
    lease = models.CharField(max_length=50,default="-")
    bill_no = models.IntegerField(null=True)
    bill_date = models.DateField(null=True,default=None)
    chalan_no = models.IntegerField(null=True)
    recieving_date_string = models.CharField(null=True,default=None,max_length=20)
    b_date = models.DateField(null=True,default=None)
    a = models.CharField(max_length=50,default="-")

    class Meta:
        db_table = 'Chemicals_Color_order'

class ChemicalsDailyConsumption(models.Model):
    con_date = models.DateField(null=True,default=None)
    color = models.ForeignKey(Color,blank=True,null=True,on_delete=models.PROTECT)
    unit = models.ForeignKey(ChemicalsUnitsMaster,blank=True,null=True,on_delete=models.PROTECT)
    quantity = models.FloatField(max_length=15)
    quantity_remaining = models.FloatField(max_length=15)
    loose_godown=models.ForeignKey(ChemicalsLooseGodownMaster,blank=True,null=True,on_delete=models.PROTECT)

    class Meta:
        db_table = 'Chemicals_Daily_consumption_details'


class ChemicalsAllOrders(models.Model):
    color = models.ForeignKey(Color,blank=True,null=True,on_delete=models.PROTECT)
    supplier = models.ForeignKey(ColorAndChemicalsSupplier,blank=True,null=True,on_delete=models.PROTECT)
    order_date = models.DateField(default=None)
    order_no = models.IntegerField()
    quantity = models.FloatField()
    rem_quantity = models.FloatField(null=True)
    rate = models.FloatField()
    amount = models.FloatField(max_length=15)
    state = models.CharField(max_length=50)
    unit = models.ForeignKey(ChemicalsUnitsMaster,blank=True,null=True,on_delete=models.PROTECT)
    bill_no = models.IntegerField(null=True)
    bill_date = models.DateField(null=True,default=None)
    validation = models.CharField(null=True,max_length=50,default="No")
    chalan_no = models.IntegerField(null=True)

    class Meta:
        db_table = 'Chemicals_Color_order_copy'

class ChemicalsGodownLooseMergeStock(models.Model):
    color = models.ForeignKey(Color,blank=True,null=True,on_delete=models.PROTECT)
    quantity = models.FloatField()
    rate = models.FloatField()
    unit = models.ForeignKey(ChemicalsUnitsMaster,blank=True,null=True,on_delete=models.PROTECT)
    state = models.ForeignKey(ChemicalsGodownsMaster,blank=True,null=True,on_delete=models.PROTECT)
    loose_godown_state = models.ForeignKey(ChemicalsLooseGodownMaster,blank=True,null=True,on_delete=models.PROTECT)

    class Meta:
        db_table = 'Chemicals_Merged_stock'

class ChemicalsClosingStock(models.Model):
    color =models.ForeignKey(Color,blank=True,null=True,on_delete=models.PROTECT)
    quantity = models.FloatField()
    rate = models.FloatField()
    unit = models.ForeignKey(ChemicalsUnitsMaster,blank=True,null=True,on_delete=models.PROTECT)
    dailydate = models.DateField(null=True,default=None)

    class Meta:
        db_table = 'Chemicals_daily_closing_stocks'


class ChemicalsClosingStockperGodown(models.Model):
    color =models.ForeignKey(Color,blank=True,null=True,on_delete=models.PROTECT)
    quantity = models.FloatField()
    rate = models.FloatField()
    unit = models.ForeignKey(ChemicalsUnitsMaster,blank=True,null=True,on_delete=models.PROTECT)
    godown=models.ForeignKey(ChemicalsGodownsMaster,blank=True,null=True,on_delete=models.PROTECT)
    loose_godown = models.ForeignKey(ChemicalsLooseGodownMaster,blank=True,null=True,on_delete=models.PROTECT)
    dailydate = models.DateField(null=True,default=None)

    class Meta:
        db_table = 'Chemicals_daily_closing_stocks_per_godown'

from django.db import models
from django.utils import timezone
from .employeeModel import *
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
class GreyCheckingCutRatesMaster(models.Model):
    cut_start_range = models.FloatField(max_length=10)
    cut_end_range = models.FloatField(max_length=10)
    checking_rate = models.FloatField(max_length=10)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Grey_Checking_Cut_Rates_Master'


class GreyGodownsMaster(models.Model):
    godown_name = models.CharField(max_length=50)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Grey_Godowns_Master'


class GreyOutprocessAgenciesMaster(models.Model):
    agency_name = models.CharField(max_length=70)
    agency_contact = PhoneNumberField(null=True)
    agency_contact_person_name = models.CharField(null=True,max_length=50)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Outprocess_Agencies_Master'

class GreyQualityMaster(models.Model):
    quality_name = models.CharField(max_length=50)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Grey_Quality_Master'

class GreySuppliersMaster(models.Model):
    id = models.AutoField(primary_key=True)
    supplier_name = models.CharField(max_length=100)
    address = models.CharField(null=True,max_length=100)
    city = models.CharField(null=True,max_length=20)
    contact_number = PhoneNumberField(null=True)
    email =  models.EmailField(max_length = 254, null= True)
    remarks = models.CharField(max_length=256)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Grey_Suppliers_Master'

class GreyTransportAgenciesMaster(models.Model):
    transport_agency_name = models.CharField(max_length=50)
    freight = models.FloatField(max_length=10)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Grey_Transport_Agencies_Master'

class OrderStatus(models.Model):
    status_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20)
    class Meta:
        db_table = 'Order_Status'

class GreyOrders(models.Model):
    order_number = models.AutoField(primary_key=True)
    order_date = models.DateField(null=False, default=timezone.now)
    grey_quality = models.ForeignKey(GreyQualityMaster,blank=False,null=False,on_delete=models.PROTECT)
    thans = models.IntegerField()
    # rate = models.FloatField()
    remarks = models.CharField(max_length=256)
    grey_supplier = models.ForeignKey(GreySuppliersMaster,blank=False,null=False,on_delete=models.PROTECT)
    order_status = models.ForeignKey(OrderStatus,blank=False,null=False,on_delete=models.PROTECT)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Grey_Orders'

class LotStatus(models.Model):
    status_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20)
    class Meta:
        db_table = 'Lot_Status'

class GreyLots(models.Model):
    grey_lot_number = models.AutoField(primary_key=True)
    order_number = models.ForeignKey(GreyOrders,blank=False,null=False,on_delete=models.PROTECT)
    lot_status = models.ForeignKey(LotStatus,blank=False,null=False,on_delete=models.PROTECT)
    bill_number = models.IntegerField()
    bill_date = models.CharField(max_length=30)
    bill_amount = models.FloatField(max_length=15)
    lr_number = models.IntegerField()
    meters = models.FloatField(max_length=15)
    bales = models.IntegerField(null=False, default=0)
    rate = models.FloatField(max_length=15,null=False, default=0.0)
    transport_agency = models.ForeignKey(GreyTransportAgenciesMaster,blank=False,null=False,on_delete=models.PROTECT)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Grey_Lots'

class Transactions(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    grey_lot = models.ForeignKey(GreyLots,blank=False,null=False,on_delete=models.PROTECT)
    lot_status = models.ForeignKey(LotStatus,blank=False,null=False,on_delete=models.PROTECT)
    created_date = models.DateField(null=False, default=timezone.now)
    modified_date = models.DateField(null=True, default=timezone.now)
    created_by = models.CharField(null=True,max_length=50)
    modified_by = models.CharField(null=True,max_length=50)
    class Meta:
        db_table = 'Transactions'

class Record(models.Model):    ########################   Main grey order
    sr_no= models.IntegerField()
    party_name= models.CharField(max_length=50,default="no")
    bill_no = models.IntegerField()
    bill_date = models.CharField(max_length=30)
    bill_amount = models.FloatField(max_length=15)
    lot_no = models.IntegerField()
    quality = models.ForeignKey(GreyQualityMaster,blank=True,null=True,on_delete=models.PROTECT)
    than = models.IntegerField()
    mtrs = models.FloatField(max_length=15)
    bale = models.IntegerField()
    rate = models.FloatField(max_length=15)
    lr_no = models.IntegerField()
    order_no = models.IntegerField()
    state_choices=(('state1','In transit'), ('state2','Order recieved'), ('state3','In godown'), ('state4','done'))
    state = models.CharField(max_length=30,default='Transit')
    bale_recieved = models.IntegerField(default=0)
    recieving_date = models.DateField(null=True, default=None)
    agency = models.ForeignKey(GreyOutprocessAgenciesMaster,blank=True,null=True,on_delete=models.PROTECT)
    total_bale = models.IntegerField()
    checker=models.ForeignKey(Employee,blank=True,null=True,on_delete=models.PROTECT)
    transport_agency=models.ForeignKey(GreyTransportAgenciesMaster,blank=True,null=True,on_delete=models.PROTECT)
    # transport_rate=models.FloatField(max_length=10,default=0)
    checking_date = models.DateField(null=True, default=None)
    processing_type = models.CharField(max_length=50,default="-")           #new
    sent_to_processing_date = models.DateField(null=True, default=None)
    arrival_location = models.ForeignKey(GreyGodownsMaster,blank=True,null=True,on_delete=models.PROTECT)          #new
    recieve_processed_date = models.DateField(null=True, default=None)
    total_thans = models.IntegerField()
    total_mtrs = models.FloatField()
    tally = models.BooleanField(default=False)
    gate_pass = models.IntegerField(null=True)
    chalan_no = models.IntegerField(null=True)

    # def __str__(self):
    #     return self.sr_no +" " +self.party_name
    class Meta:
        db_table = 'Grey_order_detais'

from django.db import models
from django.utils import timezone
from .employeeModel import *

# Create your models here.
class GreyQualityMaster(models.Model):
    qualities = models.CharField(max_length=50)

    class Meta:
        db_table = 'Grey_Quality_Master'

class ProcessingPartyNameMaster(models.Model):
    processing_party = models.CharField(max_length=50)

    class Meta:
        db_table = 'Processing_PartyName_Master'

class GreyArrivalLocationMaster(models.Model):
    location = models.CharField(max_length=50)

    class Meta:
        db_table = 'Grey_Arrival_Location_Master'

class GreyCheckerMaster(models.Model):
    checker = models.CharField(max_length=50)

class GreyCutRange(models.Model):
    range1 = models.FloatField(max_length=10)
    range2 = models.FloatField(max_length=10)
    rate = models.FloatField(max_length=10)

    class Meta:
        db_table = 'Grey_Cut_Range_Master'

class GreyTransportMaster(models.Model):
    transport = models.CharField(max_length=50)
    rate = models.FloatField(max_length=10)

    class Meta:
        db_table = 'Transport_Master'

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
    processing_party_name = models.ForeignKey(ProcessingPartyNameMaster,blank=True,null=True,on_delete=models.PROTECT)
    total_bale = models.IntegerField()
    checker=models.ForeignKey(Employee,blank=True,null=True,on_delete=models.PROTECT)
    transport=models.ForeignKey(GreyTransportMaster,blank=True,null=True,on_delete=models.PROTECT)
    # transport_rate=models.FloatField(max_length=10,default=0)
    checking_date = models.DateField(null=True, default=None)
    processing_type = models.CharField(max_length=50,default="-")           #new
    sent_to_processing_date = models.DateField(null=True, default=None)
    arrival_location = models.ForeignKey(GreyArrivalLocationMaster,blank=True,null=True,on_delete=models.PROTECT)          #new
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

class GreySupplierMaster(models.Model):
    id = models.AutoField(primary_key=True)
    supplier_name = models.CharField(max_length=100)
    address = models.CharField(null=True,max_length=100)
    city = models.CharField(null=True,max_length=20)
    remarks = models.CharField(max_length=256)
    class Meta:
        db_table = 'Grey_Supplier_Master'


class GreyOrder(models.Model):
    order_number = models.AutoField(primary_key=True)
    grey_quality = models.ForeignKey(GreyQualityMaster,blank=False,null=False,on_delete=models.PROTECT)
    thans = models.IntegerField()
    rate = models.FloatField()
    average_cut = models.FloatField()
    remarks = models.CharField(max_length=256)
    supplier = models.ForeignKey(GreySupplierMaster,blank=False,null=False,on_delete=models.PROTECT)
    class Meta:
        db_table = 'Grey_Order'

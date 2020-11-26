from django.db import models
from django.utils import timezone


# Create your models here.
class Quality(models.Model):
    qualities = models.CharField(max_length=50)

    

class Record(models.Model):
    sr_no= models.IntegerField()
    party_name= models.CharField(max_length=50,default="no")
    bill_no = models.IntegerField()
    bill_date = models.CharField(max_length=30)
    bill_amount = models.FloatField(max_length=15)
    lot_no = models.IntegerField() 
    quality = models.CharField(max_length=100)
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
    processing_party_name = models.CharField(max_length=50,default="-")
    total_bale = models.IntegerField()
    checker=models.CharField(max_length=50,default="-")
    checking_date = models.DateField(null=True, default=None)
    processing_type = models.CharField(max_length=50,default="-")           #new
    sent_to_processing_date = models.DateField(null=True, default=None)
    arrival_location = models.CharField(max_length=50,default="-")          #new
    recieve_processed_date = models.DateField(null=True, default=None)
    total_thans = models.IntegerField()
    total_mtrs = models.FloatField()
    tally = models.BooleanField(default=False)
    gate_pass = models.IntegerField(null=True)
    chalan_no = models.IntegerField(null=True)
    
    # def __str__(self):
    #     return self.sr_no +" " +self.party_name



class ProcessingPartyName(models.Model):
    processing_party = models.CharField(max_length=50)

class ArrivalLocation(models.Model):
    location = models.CharField(max_length=50)

class Checker(models.Model):
    checker = models.CharField(max_length=50)

class ThanRange(models.Model):
    range1 = models.FloatField(max_length=10)
    range2 = models.FloatField(max_length=10)
    rate = models.FloatField(max_length=10)

######################################       COLOR      ##########################################
class ColorSupplier(models.Model):
    supplier = models.CharField(max_length=50)
    address = models.CharField(null=True,max_length=100)
    city = models.CharField(null=True,max_length=20)

class Color(models.Model):
    color = models.CharField(max_length=50)
    quantity = models.FloatField(max_length=15,default=0.0)

class Godowns(models.Model):
    godown = models.CharField(max_length=50)

class Lease(models.Model):
    lease = models.CharField(max_length=50)

class Units(models.Model):
    unit = models.CharField(max_length=50)

class ColorRecord(models.Model):
    color = models.CharField(max_length=50)
    supplier = models.CharField(max_length=50)
    order_date = models.DateField(default=None)
    order_no = models.IntegerField()
    quantity = models.IntegerField()
    unit = models.CharField(null=True,max_length=50)
    rate = models.FloatField()
    amount = models.FloatField(max_length=15)
    state = models.CharField(max_length=50)
    recieving_date = models.DateField(null=True,default=None)
    total_quantity = models.IntegerField()
    godown = models.CharField(max_length=50,default="-")
    lease = models.CharField(max_length=50,default="-")
    bill_no = models.IntegerField(null=True)
    bill_date = models.DateField(null=True,default=None)
    chalan_no = models.IntegerField(null=True)
    a_date = models.DateField(null=True,default=None)
    b_date = models.DateField(null=True,default=None)
    a = models.CharField(max_length=50,default="-")

class DailyConsumption(models.Model):
    con_date = models.DateField(null=True,default=None)
    color = models.CharField(max_length=50,default="-")
    unit = models.CharField(null=True,max_length=50)
    quantity = models.FloatField(max_length=15)
    quantity_remaining = models.FloatField(max_length=15)

class AllOrders(models.Model):
    color = models.CharField(max_length=50)
    supplier = models.CharField(max_length=50)
    order_date = models.DateField(default=None)
    order_no = models.IntegerField()
    quantity = models.IntegerField()
    rem_quantity = models.IntegerField(null=True)
    rate = models.FloatField()
    amount = models.FloatField(max_length=15)
    state = models.CharField(max_length=50)
    unit = models.CharField(null=True,max_length=50)
    bill_no = models.IntegerField(null=True)
    bill_date = models.DateField(null=True,default=None)
    validation = models.CharField(null=True,max_length=50)
    chalan_no = models.IntegerField(null=True)

class GodownLeaseColors(models.Model):
    color = models.CharField(max_length=50)
    quantity = models.IntegerField()
    rate = models.FloatField()
    unit = models.CharField(null=True,max_length=50)
    state = models.CharField(max_length=50)

class ClosingStock(models.Model):
    color = models.CharField(max_length=50)
    quantity = models.IntegerField()
    rate = models.FloatField()
    unit = models.CharField(null=True,max_length=50)
    dailydate = models.DateField(null=True,default=None)
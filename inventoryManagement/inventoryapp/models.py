from django.db import models
from django.utils import timezone


# Create your models here.
class GreyQualityMaster(models.Model):
    qualities = models.CharField(max_length=50)

class ProcessingPartyNameMaster(models.Model):
    processing_party = models.CharField(max_length=50)

class GreyArrivalLocationMaster(models.Model):
    location = models.CharField(max_length=50)

class GreyCheckerMaster(models.Model):
    checker = models.CharField(max_length=50)

class GreyCutRange(models.Model):
    range1 = models.FloatField(max_length=10)
    range2 = models.FloatField(max_length=10)
    rate = models.FloatField(max_length=10)

class GreyTransportMaster(models.Model):
    transport = models.CharField(max_length=50)
    rate = models.FloatField(max_length=10)
    

class Record(models.Model):
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
    checker=models.ForeignKey(GreyCheckerMaster,blank=True,null=True,on_delete=models.PROTECT) 
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
    color = models.ForeignKey(Color,blank=True,null=True,on_delete=models.PROTECT)
    supplier = models.ForeignKey(ColorSupplier,blank=True,null=True,on_delete=models.PROTECT)
    order_date = models.DateField(default=None)
    order_no = models.IntegerField()
    quantity = models.FloatField()
    unit = models.ForeignKey(Units,blank=True,null=True,on_delete=models.PROTECT)
    rate = models.FloatField()
    amount = models.FloatField(max_length=15)
    state = models.CharField(max_length=50)
    recieving_date = models.DateField(null=True,default=None)
    total_quantity = models.FloatField()
    godown = models.ForeignKey(Godowns,blank=True,null=True,on_delete=models.PROTECT)
    lease = models.CharField(max_length=50,default="-")
    bill_no = models.IntegerField(null=True)
    bill_date = models.DateField(null=True,default=None)
    chalan_no = models.IntegerField(null=True)
    recieving_date_string = models.CharField(null=True,default=None,max_length=20)
    b_date = models.DateField(null=True,default=None)
    a = models.CharField(max_length=50,default="-")

class DailyConsumption(models.Model):
    con_date = models.DateField(null=True,default=None)
    color = models.CharField(max_length=50,default="-")
    unit = models.CharField(null=True,max_length=50)
    quantity = models.FloatField(max_length=15)
    quantity_remaining = models.FloatField(max_length=15)

class AllOrders(models.Model):
    color = models.ForeignKey(Color,blank=True,null=True,on_delete=models.PROTECT)
    supplier = models.ForeignKey(ColorSupplier,blank=True,null=True,on_delete=models.PROTECT)
    order_date = models.DateField(default=None)
    order_no = models.IntegerField()
    quantity = models.FloatField()
    rem_quantity = models.FloatField(null=True)
    rate = models.FloatField()
    amount = models.FloatField(max_length=15)
    state = models.CharField(max_length=50)
    unit = models.ForeignKey(Units,blank=True,null=True,on_delete=models.PROTECT)
    bill_no = models.IntegerField(null=True)
    bill_date = models.DateField(null=True,default=None)
    validation = models.CharField(null=True,max_length=50,default="No")
    chalan_no = models.IntegerField(null=True)

class GodownLeaseColors(models.Model):
    color = models.CharField(max_length=50)
    quantity = models.FloatField()
    rate = models.FloatField()
    unit = models.CharField(null=True,max_length=50)
    state = models.CharField(max_length=50)

class ClosingStock(models.Model):
    color = models.CharField(max_length=50)
    quantity = models.FloatField()
    rate = models.FloatField()
    unit = models.CharField(null=True,max_length=50)
    dailydate = models.DateField(null=True,default=None)


################################Employeee###############
class Employee(models.Model):
    name = models.CharField(max_length=50)
    father_name = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=50)
    account_no = models.CharField(max_length=12)
    ifsc = models.CharField(max_length=11)
    account_type =models.CharField(max_length=50)
    aadhar_no = models.CharField(max_length=12)
    contractor_name = models.CharField(max_length=50)
    phone_no = models.CharField(max_length=10)
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    

class CompanyAccounts(models.Model):
    company_account = models.CharField(max_length=11)
    account_name = models.CharField(max_length=50)
    ifsc = models.CharField(null=True,max_length=11)
    bank_name = models.CharField(null=True,max_length=50)
    branch_code = models.CharField(max_length=50,default="")
    account_type = models.CharField(max_length=50,default="Savings")

class MonthlyPayment(models.Model):
    employee = models.ForeignKey(Employee,blank=True,null=True,on_delete=models.PROTECT)
    payment_date = models.DateField(null=True,default=None)
    company_account = models.ForeignKey(CompanyAccounts,blank=True,null=True,on_delete=models.PROTECT)
    amount = models.FloatField()
    last_payment_date = models.DateField(null=True,default=None)

class CityMaster(models.Model):
   city = models.CharField(null=True,max_length=50)
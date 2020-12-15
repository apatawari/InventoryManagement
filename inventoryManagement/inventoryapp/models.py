from django.db import models
from django.utils import timezone


################################Employeee###############
class CityMaster(models.Model):
    city = models.CharField(null=True,max_length=50)

class Employee(models.Model):
    name = models.CharField(max_length=50)
    father_name = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=50)
    account_no = models.CharField(max_length=50)
    ifsc = models.CharField(max_length=50)
    account_type =models.CharField(max_length=50)
    aadhar_no = models.CharField(max_length=50)
    contractor_name = models.CharField(max_length=50)
    phone_no = models.CharField(max_length=10)
    address = models.CharField(max_length=50)
    city = models.ForeignKey(CityMaster,blank=True,null=True,on_delete=models.PROTECT)
    employee_category = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'Employee_master'

class CompanyAccounts(models.Model):
    company_account = models.CharField(max_length=50)
    account_name = models.CharField(max_length=50)
    ifsc = models.CharField(null=True,max_length=50)
    bank_name = models.CharField(null=True,max_length=50)
    branch_code = models.CharField(max_length=50,default="")
    account_type = models.CharField(max_length=50,default="Savings")

    class Meta:
        db_table = 'Company_bank_accounts_master'

class MonthlyPayment(models.Model):
    employee = models.ForeignKey(Employee,blank=True,null=True,on_delete=models.PROTECT)
    payment_date = models.DateField(null=True,default=None)
    company_account = models.ForeignKey(CompanyAccounts,blank=True,null=True,on_delete=models.PROTECT)
    amount = models.FloatField()
    last_payment_date = models.DateField(null=True,default=None)

    class Meta:
        db_table = 'Employee_salary_details'

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


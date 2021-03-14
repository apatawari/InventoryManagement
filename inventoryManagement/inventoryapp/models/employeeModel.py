from django.db import models
from django.utils import timezone
from .commonModel import CityMaster
################################Employeee###############



class EmployeeCategoryMaster(models.Model):
    category = models.CharField(null=True,max_length=50)

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
    category = models.ForeignKey(EmployeeCategoryMaster,blank=True,null=True,on_delete=models.PROTECT)

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

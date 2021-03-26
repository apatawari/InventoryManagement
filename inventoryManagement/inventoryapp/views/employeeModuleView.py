from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Employee,CompanyAccounts,ChemicalsClosingStockperGodown,MonthlyPayment,GreyTransportAgenciesMaster,CityMaster,EmployeeCategoryMaster
from inventoryapp.resources import ItemResources
from inventoryapp.filters import RecordFilter,ColorFilter,ColorOrderFilter,GodownLeaseFilter,EmployeeFilter
from django.contrib import messages
from tablib import Dataset
from django.http import HttpResponseRedirect
import pandas
import numpy as np
import datetime
import dateutil.parser
import xlwt
import ast
from django.template.loader import render_to_string

##################################### Module 3 - Employee Start ######################################

################ ADD CITY MASTER ####################
def renderAddCity(request):
    parties_all = CityMaster.objects.all().order_by('city')

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    cities = paginator.get_page(page)
    return render(request,'./EmployeeModule/addcity.html',{'records':cities})

def saveCity(request):
    p = request.POST.get("city_name")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(CityMaster,city=p)
        messages.error(request,"This City already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addcity')
        new_Party = CityMaster(
            city= p
        )
        new_Party.save()
        messages.success(request,"City added successfully")
    return redirect('/addcity')

def deleteCity(request,id):
    try:
        CityMaster.objects.filter(id=id).delete()
        messages.success(request,"City deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addcity')

def renderEditCity(request,id):
    party=get_object_or_404(CityMaster,id=id)
    return render(request,'./EmployeeModule/editcity.html',{'id':id,'name':party.city})

def editCity(request,id):
    party=get_object_or_404(CityMaster,id=id)
    p=request.POST.get("edit-city")
    p = p.upper()
    p = p.strip()
    party.city = p
    party.save()
    messages.success(request,"City edited")
    return redirect('/addcity')

################ employee category master ######################

def renderAddEmpCategory(request):
    parties_all = EmployeeCategoryMaster.objects.all().order_by('category')

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    cities = paginator.get_page(page)
    return render(request,'./EmployeeModule/addemployeecategory.html',{'records':cities})

def saveEmpCategory(request):
    q=request.POST.get("ada")
    p = request.POST.get("emp-category")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(EmployeeCategoryMaster,category=p)
        messages.error(request,"This Category already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addemployeecategory')
        new_Party = EmployeeCategoryMaster(
            category= p
        )
        new_Party.save()
        messages.success(request,"Category added successfully")
    return redirect('/addemployeecategory')

def deleteEmpCategory(request,id):
    try:
        EmployeeCategoryMaster.objects.filter(id=id).delete()
        messages.success(request,"Category deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addemployeecategory')

def renderEditEmpCategory(request,id):
    party=get_object_or_404(EmployeeCategoryMaster,id=id)
    return render(request,'./EmployeeModule/editemployeecategory.html',{'id':id,'name':party.category})

def editEmpCategory(request,id):
    party=get_object_or_404(EmployeeCategoryMaster,id=id)
    p=request.POST.get("edit-category")
    p = p.upper()
    p = p.strip()
    party.category = p
    party.save()
    messages.success(request,"Category edited")
    return redirect('/addemployeecategory')


#################### EMPLOYEE HOME ######################
def employeehome(request):
    emp=Employee.objects.filter(employee_category='Contractor staff').order_by('name')
    cities = CityMaster.objects.all().order_by('city')
    empcat=EmployeeCategoryMaster.objects.all().order_by('category')
    return render(request, './EmployeeModule/employeehome.html',{'city':cities,'emp':emp,'empcat':empcat})

################### ADD NEW EMPLOYEE ####################
def saveEmployee(request):
    if(len(request.POST.get('phone_no'))>10 or len(request.POST.get('phone_no'))<10):
        messages.error(request,"Enter valid details")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    c_id=int(request.POST.get('city'))
    city=get_object_or_404(CityMaster,id=c_id)
    try:
        emp=get_object_or_404(Employee,
            name = request.POST.get('name'),
            father_name = request.POST.get('father_name'),
            bank_name = request.POST.get('bank_name'),
            account_no = (request.POST.get('account_no')),
            ifsc = request.POST.get('ifsc_code'),
            account_type = request.POST.get('account_type'),
            aadhar_no = (request.POST.get('aadhar_no')),
            contractor_name = request.POST.get('contractor_name'),
            phone_no = (request.POST.get('phone_no')),
            address = request.POST.get('address'),
            city = city

        )
        messages.error(request,"This Employee Already Exists")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except:
        pass
    new_emp = Employee(
        name = (request.POST.get('name')).title(),
        father_name = (request.POST.get('father_name')).title(),
        bank_name = (request.POST.get('bank_name')).upper(),
        account_no = (request.POST.get('account_no')),
        ifsc = (request.POST.get('ifsc_code')).upper(),
        account_type = request.POST.get('account_type'),
        aadhar_no = (request.POST.get('aadhar_no')),
        contractor_name = request.POST.get('contractor_name'),
        phone_no = (request.POST.get('phone_no')),
        address = (request.POST.get('address')).title(),
        city = city,
        employee_category=request.POST.get('employeetype'),
        category=get_object_or_404(EmployeeCategoryMaster,id=int(request.POST.get('emp-cat')))
        )
    new_emp.save()
    messages.success(request,"Employee Added")
    return redirect('/employeehome')

############### VIEW ALL EMPLOYEES #################
def employeedetails(request):
    employees = Employee.objects.all().order_by('name')
    records_filter = EmployeeFilter(request.GET,queryset=employees)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    emps = paginator.get_page(page)
    categories=EmployeeCategoryMaster.objects.all().order_by('category')
    return render(request, './EmployeeModule/employeedetails.html',{'records':emps,'filter':records_filter,'categories':categories})

########## DELETE EMPLOYEE ############
def deleteEmployee(request,id):
    Employee.objects.filter(id=id).delete()
    messages.success(request,'Employee Deleted')
    return redirect('/employeedetails')

########### EDIT EMPLOYEE ############
def renderEditEmployee(request,id):
    emp=get_object_or_404(Employee,id=id)
    employees=Employee.objects.filter(employee_category='Contractor staff').order_by('name')
    cities = CityMaster.objects.all().order_by('city')
    empcat=EmployeeCategoryMaster.objects.all().order_by('category')
    return render(request,'./EmployeeModule/editemployee.html',{'emp':emp,'employees':employees,'city':cities,'empcat':empcat})

def saveEditEmployee(request,id):
    c_id = int(request.POST.get('city'))
    city = get_object_or_404(CityMaster,id=c_id)
    emp=get_object_or_404(Employee,id=id)
    emp.name= (request.POST.get('name')).title()
    emp.father_name = (request.POST.get('father_name')).title()
    emp.bank_name = (request.POST.get('bank_name')).upper()
    emp.account_no = (request.POST.get('account_no'))
    emp.ifsc = (request.POST.get('ifsc_code')).upper()
    emp.account_type = request.POST.get('account_type')
    emp.aadhar_no = (request.POST.get('aadhar_no'))
    emp.contractor_name = request.POST.get('contractor_name')
    emp.phone_no = (request.POST.get('phone_no'))
    emp.address = (request.POST.get('address')).upper()
    emp.city = city
    emp.employee_category=request.POST.get('employeetype')
    emp.category = get_object_or_404(EmployeeCategoryMaster,id=int(request.POST.get('emp-cat')))
    emp.save()
    messages.success(request,"Employee details are saved")
    return redirect('/employeedetails')

############## BANK MASTER #############
def renderAddBankAc(request):
    all_checker = CompanyAccounts.objects.all().order_by('bank_name')
    #return render(request,'./GreyModule/addquality.html',{'allqualities':all_qualities})
    paginator = Paginator(all_checker,10)
    page = request.GET.get('page')
    checkers = paginator.get_page(page)

    return render(request,'./EmployeeModule/addbank.html',{'records':checkers})

def saveBank(request):
    q=request.POST.get("bank_name")
    q = q.strip()
    l=(request.POST.get("account_no"))

    m=request.POST.get("ifsc")
    m = m.strip()
    n=request.POST.get("account_name")
    n = n.strip()
    o=request.POST.get("branch_code")
    o = o.strip()
    p=request.POST.get("account_type")
    p = p.strip()
    try:
        existing_quality=get_object_or_404(CompanyAccounts,bank_name=q.upper(),account_no=l,ifsc=m.upper())
        messages.error(request,"This checker already exists")
    except:
        if q.strip()=="" or m=="" or n=="" or o=="" or p=="":
            messages.error(request,"please enter valid input")
            return redirect('/addbank')
        new_quality = CompanyAccounts(
            company_account = l,
            account_name = n.upper(),
            ifsc = m.upper(),
            bank_name = q.upper(),
            account_type=p.upper(),
            branch_code=o.upper()
        )
        new_quality.save()
        messages.success(request,"Bank account added")
    return redirect('/addbank')

def deleteBank(request,id):
    try:
        CompanyAccounts.objects.filter(id=id).delete()
        messages.success(request,"Bank deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addbank')

def renderEditBank(request,id):
    quality=get_object_or_404(CompanyAccounts,id=id)
    return render(request,'./EmployeeModule/editbank.html',{'id':id,'record':quality})

def editBank(request,id):
    quality=get_object_or_404(CompanyAccounts,id=id)
    q=request.POST.get("bank_name")
    q = q.strip()
    l=request.POST.get("account_no")

    m=request.POST.get("ifsc")
    m = m.strip()
    n=request.POST.get("account_name")
    # n = n.strip()

    if q.strip()=="" or m=="" or n=="":
        messages.error(request,"please enter valid input")
        return redirect('/addbank')
    quality.bank_name = q.upper()
    quality.company_account = l
    quality.ifsc = m.upper()
    quality.account_name = n.upper()
    quality.save()
    messages.success(request,"Account edited")
    return redirect('/addbank')
############## BANK MASTER END ############

########### PAYMENT TO EMPLOYEE FORM ###############
def renderGeneratorForm(request):
    emps = Employee.objects.all().order_by('name')
    banks = CompanyAccounts.objects.all().order_by('bank_name')
    d=str(datetime.date.today())


    # pay=MonthlyPayment.objects.all()
    # for p in pay:
    #     print(p.employee.name,p.company_account.bank_name)
    return render(request,'./EmployeeModule/generatorform.html',{'emps':emps,'banks':banks,'d':d})

def generatePayment(request):
    payment_date = str(request.POST.get('payment_date'))
    bank_id = int(request.POST.get('bank'))
    bank = get_object_or_404(CompanyAccounts,id=bank_id)
    emps = Employee.objects.all().order_by('name')
    selected_emps=[]
    for e in emps:
        if(request.POST.get(str(e.phone_no))!=None):
            selected_emps.append(int(request.POST.get(str(e.phone_no))))
    print(selected_emps,bank.bank_name,payment_date)

    selected_employee = Employee.objects.filter(id__in=selected_emps).order_by('name')


    return render(request,'./EmployeeModule/payemployee.html',{'idlist':selected_emps,'employee':selected_employee,'bank':bank,'d':payment_date})

def makePayment(request):
    selected_emp=request.POST.get("selected-emp-id")
    selected_emp = ast.literal_eval(selected_emp)
    bankid = int(request.POST.get('bankid'))
    bank=get_object_or_404(CompanyAccounts,id=bankid)
    payment_date = request.POST.get("paydate")
    print(selected_emp,payment_date,bank.bank_name)

    for e_id in selected_emp:
        emp=get_object_or_404(Employee,id=int(e_id))
        if(request.POST.get(str(emp.phone_no))==""):
            continue
        try:
            last_pay = MonthlyPayment.objects.filter(employee=emp).order_by('-payment_date').first()
            last_pay_date = last_pay.payment_date
        except:
            last_pay_date = payment_date
        new_payment = MonthlyPayment(
            employee=emp,
            company_account = bank,
            payment_date = payment_date,
            amount=float(request.POST.get(str(emp.phone_no))),
            last_payment_date=last_pay_date
        )
        new_payment.save()
    return redirect('/banksheet')


########### SHOW BANK SHEET ################
def bankSheet(request):
    payments=MonthlyPayment.objects.all().order_by('-payment_date')
    return render(request,'./EmployeeModule/banksheet.html',{'payments':payments})

########### SHOW BANK SHEET W.R.T. DATE################
def bankSheet2(request):
    begin = request.POST.get("start_date")
    end = request.POST.get("end_date")
    if(begin!="" or end!=""):

        begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
        end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
        selected_dates=[]

        next_day = begin
        while True:
            if next_day > end:
                break
            selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
            next_day += datetime.timedelta(days=1)


        payments=MonthlyPayment.objects.filter(payment_date__in=selected_dates).order_by('payment_date')
        begin=str(begin)
        end=str(end)

        return render(request,'./EmployeeModule/banksheet.html',{'payments':payments,'begin':begin,'end':end})

################# DISPLAY SALARY SHEET ################
def salarySheet(request):
    payments=MonthlyPayment.objects.all().order_by('-payment_date')
    return render(request,'./EmployeeModule/salarysheet.html',{'payments':payments})

################# DISPLAY SALARY SHEET W.R.T. Date ################
def salarySheet2(request):
    begin = request.POST.get("start_date")
    end = request.POST.get("end_date")
    if(begin!="" or end!=""):

        begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
        end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
        selected_dates=[]

        next_day = begin
        while True:
            if next_day > end:
                break
            selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
            next_day += datetime.timedelta(days=1)


        payments=MonthlyPayment.objects.filter(payment_date__in=selected_dates).order_by('payment_date')

        begin=str(begin)
        end=str(end)
        return render(request,'./EmployeeModule/salarysheet.html',{'payments':payments,'begin':begin,'end':end})

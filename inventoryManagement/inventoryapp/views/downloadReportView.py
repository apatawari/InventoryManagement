from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,GreyQualitiesMaster,GreyCheckingCutRatesMaster,GreyOutprocessAgenciesMaster,GreyGodownsMaster,ColorAndChemicalsSupplier,Color,ColorRecord,ChemicalsDailyConsumption,ChemicalsAllOrders,ChemicalsGodownLooseMergeStock,ChemicalsGodownsMaster,ChemicalsLooseGodownMaster,ChemicalsUnitsMaster,ChemicalsClosingStock
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



############################# Download Records in Excel Files (GREY, COLOR & CHEMICAL) #######################################

def export_page_xls(request):
    ur=request.META.get('HTTP_REFERER')
    ur=ur.split('?')
    stateur=ur[0]
    stateur=stateur.split('/')
    stateur=stateur[-1]
    if(stateur=="intransit"):
        file_name="Intransit"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Total Bale', 'Rate', 'LR No', 'Order No', 'State' ]
        records_list=Record.objects.filter(state="Transit").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'state')

    elif(stateur=="godown"):
        file_name="Godown"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'State' ]
        records_list=Record.objects.filter(state="Godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    elif(stateur=="checking"):
        file_name="Checked"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'Checking Date', 'State','Checker Name','Transport Agency' ]
        records_list=Record.objects.filter(state="Checked").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'lr_no', 'order_no', 'recieving_date', 'checking_date', 'state','checker__name','transport__transport')
    elif(stateur=="inprocess"):
        file_name="InProcess"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Checking Date', 'Sent to Processing Date', 'State', 'Processing Type', 'Processing Party' ]
        records_list=Record.objects.filter(state="In Process").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'checking_date', 'sent_to_processing_date', 'state', 'processing_type', 'agency_name__agency_name')
    elif (stateur=="readytoprint"):
        file_name="ProcessedGrey"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Sent to Processing Date', 'Processed Date', 'Processing Type', 'Arrival location', 'State' ]
        records_list=Record.objects.filter(state="Ready to print").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'sent_to_processing_date', 'recieve_processed_date', 'processing_type', 'arrival_location__location', 'state')
######################## color & chemical download #############################
    elif(stateur=="goodsreceived"):
        file_name="Godown Stock"
        columns=['chemical','quantity','unit','average rate(Rs)','godown name']
        godowns=ChemicalsGodownsMaster.objects.all()
        godowns_list=[]
        for g in godowns:
            godowns_list.append(g)
        records_list = ChemicalsGodownLooseMergeStock.objects.filter(state__in=godowns_list,loose_godown_state=None).exclude(quantity=0).values_list('color__color','quantity','unit__unit','rate','state__godown')

    elif(stateur=="goodslease"):
        file_name="Loose Godown Stock"
        columns=['chemical','quantity','unit','average rate(Rs)','loose godown name']
        lease=ChemicalsLooseGodownMaster.objects.all()
        lease_list=[]
        for g in lease:
            lease_list.append(g)
        records_list = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state__in=lease_list).values_list('color__color','quantity','unit__unit','rate','loose_godown_state__lease')
    else:
        file_name="Color Orders"
        columns = ['Supplier Name', 'order no', 'order Date', 'chemical', 'quantity', 'quantity remaining', 'unit', 'rate', 'order amount', 'Bill verify','state']
        records_list=ChemicalsAllOrders.objects.all().values_list('supplier__supplier', 'order_no', 'order_date', 'color__color', 'quantity', 'rem_quantity', 'unit__unit', 'rate', 'amount', 'validation', 'state')


    # ur=request.META.get('HTTP_REFERER')

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s.xls'%file_name

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Grey Data') # this will make a sheet named Users Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True


    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style) # at 0 row 0 column

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    #prev url req string to dict to querydict
    # ur=ur.split('?')
    if(len(ur)==2):

        l=ur[1]
        l=l.split('&')
        if(len(l)<3):
            l0=l[0]
            l0=l0.split('=')
            dic1={l0[0]:l0[1]}
            page=l0[1]
        elif(len(l)==3):
            l0=l[0]
            l0=l0.split('=')
            party=l0[1]
            l0[1]=party.replace('+',' ')
            l1=l[1]
            l1=l1.split('=')
            l2=l[2]
            l2=l2.split('=')
            party=l2[1]
            l2[1]=party.replace('+',' ')
            dic1={'page':'1',l0[0]:l0[1],l1[0]:l1[1],l2[0]:l2[1]}
            page=1
        else:
            l0=l[0]
            l0=l0.split('=')
            l1=l[1]
            l1=l1.split('=')
            party=l1[1]
            l1[1]=party.replace('+',' ')
            l2=l[2]
            l2=l2.split('=')
            l3=l[3]
            l3=l3.split('=')
            party=l3[1]
            l3[1]=party.replace('+',' ')
            dic1={l0[0]:l0[1],l1[0]:l1[1],l2[0]:l2[1],l3[0]:l3[1]}
            page=l0[1]

    else:
        dic1={'page':'1','party_name':'','lot_no':'','quality':''}

    d=QueryDict('',mutable=True)
    d.update(dic1)

    print(d)

    records_filter = RecordFilter(d,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})
    paginator = Paginator(records_filter.qs,20)
    page = d.get('page')
    page=int(page)

    records = paginator.get_page(page)
    # rows = Record.objects.filter(state="godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    for row in records:
        row_num += 1
        for col_num in range(len(row)):

            ws.write(row_num, col_num, str(row[col_num]), font_style)

    wb.save(response)

    return response


def export_filter_all_xls(request):
    ur=request.META.get('HTTP_REFERER')

    ur=ur.split('?')
    stateur=ur[0]
    stateur=stateur.split('/')
    stateur=stateur[-1]
    if(stateur=="intransit"):
        file_name="Intransit-filt"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Total Bale', 'Rate', 'LR No', 'Order No', 'State' ]
        records_list=Record.objects.filter(state="Transit").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'state')

    elif(stateur=="godown"):
        file_name="Godown-filt"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'State' ]
        records_list=Record.objects.filter(state="Godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    elif(stateur=="checking"):
        file_name="Checked-filt"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'Checking Date', 'State' ,'Checker name','Transport' ]
        records_list=Record.objects.filter(state="Checked").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'lr_no', 'order_no', 'recieving_date', 'checking_date', 'state','checker__name', 'transport__transport')
    elif(stateur=="inprocess"):
        file_name="InProcess-filt"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Checking Date', 'Sent to Processing Date', 'State', 'Processing Type', 'Processing Party' ]
        records_list=Record.objects.filter(state="In Process").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'checking_date', 'sent_to_processing_date', 'state', 'processing_type', 'agency_name__agency_name')
    elif (stateur=="readytoprint"):
        file_name="ProcessedGrey-filt"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Sent to Processing Date', 'Processed Date', 'Processing Type', 'Arrival location', 'State' ]
        records_list=Record.objects.filter(state="Ready to print").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'sent_to_processing_date', 'recieve_processed_date', 'processing_type', 'arrival_location__location', 'state')
    ######color
    elif(stateur=="goodsreceived"):
        file_name="Godown Stock"
        columns=['chemical','quantity','unit','average rate(Rs)','godown name']
        godowns=ChemicalsGodownsMaster.objects.all()
        godowns_list=[]
        for g in godowns:
            godowns_list.append(g)
        records_list = ChemicalsGodownLooseMergeStock.objects.filter(state__in=godowns_list,loose_godown_state=None).exclude(quantity=0).values_list('color__color','quantity','unit__unit','rate','state__godown')

    elif(stateur=="goodslease"):
        file_name="Loose Godown Stock"
        columns=['chemical','quantity','unit','average rate(Rs)','loose godown name']
        lease=ChemicalsLooseGodownMaster.objects.all()
        lease_list=[]
        for g in lease:
            lease_list.append(g)
        records_list = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state__in=lease_list).values_list('color__color','quantity','unit__unit','rate','loose_godown_state__lease')
    elif (stateur=="ordergeneration"):
        file_name="Color Orders"
        columns = ['Supplier Name', 'order no', 'order Date', 'chemical', 'quantity', 'quantity remaining', 'unit', 'rate', 'order amount', 'Bill verify','state']
        records_list=ChemicalsAllOrders.objects.all().values_list('supplier__supplier', 'order_no', 'order_date', 'color__color', 'quantity', 'rem_quantity', 'unit__unit', 'rate', 'amount', 'validation', 'state')
    elif (stateur=="banksheetfiltered"):
        file_name="Bank Sheet"
        begin = request.POST.get("start_date1")
        end = request.POST.get("end_date1")
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

            # columns = ['Ref No', 'Amount', 'Value Date', 'Branch Code', 'Sender Account type', 'Remitter account no', 'IFSC Code', 'Debit Account', 'Benificiary Account type', 'Bank Account No','Benificiary Name','Remittance Details','Debit Account System','Originator of Remittance','Mobile No']
            columns = [ 'Amount', 'Value Date', 'Branch Code', 'Sender Account type', 'Remitter account no', 'IFSC Code', 'Benificiary Account type', 'Bank Account No','Benificiary Name','Mobile No']
            records_list=MonthlyPayment.objects.filter(payment_date__in=selected_dates).values_list('amount', 'payment_date', 'company_account__branch_code', 'company_account__account_type', 'company_account__company_account', 'employee__ifsc', 'employee__account_type', 'employee__account_no', 'employee__name', 'employee__phone_no').order_by('payment_date')
    elif(stateur=="banksheet"):

        file_name="Bank Sheet"
        # columns = ['Ref No', 'Amount', 'Value Date', 'Branch Code', 'Sender Account type', 'Remitter account no', 'IFSC Code', 'Debit Account', 'Benificiary Account type', 'Bank Account No','Benificiary Name','Remittance Details','Debit Account System','Originator of Remittance','Mobile No']
        columns = [ 'Amount', 'Value Date', 'Branch Code', 'Sender Account type', 'Remitter account no', 'IFSC Code', 'Benificiary Account type', 'Bank Account No','Benificiary Name','Mobile No']
        records_list=MonthlyPayment.objects.all().values_list('amount', 'payment_date', 'company_account__branch_code', 'company_account__account_type', 'company_account__company_account', 'employee__ifsc', 'employee__account_type', 'employee__account_no', 'employee__name', 'employee__phone_no').order_by('payment_date')

    elif(stateur=="salarysheet"):

        file_name="Salary Sheet"
        # columns = ['Ref No', 'Amount', 'Value Date', 'Branch Code', 'Sender Account type', 'Remitter account no', 'IFSC Code', 'Debit Account', 'Benificiary Account type', 'Bank Account No','Benificiary Name','Remittance Details','Debit Account System','Originator of Remittance','Mobile No']
        columns = [ 'Name', 'Father Name', 'Bank Name', 'Account No', 'IFSC Code', 'Amount', 'Aadhar No','Contractor Name','Phone No','Address','City','Payment date']
        records_list=MonthlyPayment.objects.all().values_list('employee__name', 'employee__father_name', 'employee__bank_name', 'employee__account_no', 'employee__ifsc', 'amount', 'employee__aadhar_no', 'employee__contractor_name', 'employee__phone_no','employee__address','employee__city','payment_date').order_by('payment_date')

    elif (stateur=="salarysheetfiltered"):
        file_name="Salary Sheet"
        begin = request.POST.get("start_date1")
        end = request.POST.get("end_date1")
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



            # columns = ['Ref No', 'Amount', 'Value Date', 'Branch Code', 'Sender Account type', 'Remitter account no', 'IFSC Code', 'Debit Account', 'Benificiary Account type', 'Bank Account No','Benificiary Name','Remittance Details','Debit Account System','Originator of Remittance','Mobile No']
            columns = [ 'Name', 'Father Name', 'Bank Name', 'Account No', 'IFSC Code', 'Amount', 'Aadhar No','Contractor Name','Phone No','Address','City','Payment date']
            records_list=MonthlyPayment.objects.filter(payment_date__in=selected_dates).values_list('employee__name', 'employee__father_name', 'employee__bank_name', 'employee__account_no', 'employee__ifsc', 'amount', 'employee__aadhar_no', 'employee__contractor_name', 'employee__phone_no','employee__address','employee__city','payment_date').order_by('payment_date')


    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s.xls'%file_name

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Godown Data') # this will make a sheet named Users Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True


    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style) # at 0 row 0 column

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    #prev url req string to dict to querydict
    # ur=ur.split('?')
    if(len(ur)==2):

        l=ur[1]
        l=l.split('&')
        if(len(l)<3):
            l0=l[0]
            l0=l0.split('=')
            dic1={l0[0]:l0[1]}
            page=l0[1]
        elif(len(l)==3):
            l0=l[0]
            l0=l0.split('=')
            party=l0[1]
            l0[1]=party.replace('+',' ')
            l1=l[1]
            l1=l1.split('=')
            l2=l[2]
            l2=l2.split('=')
            party=l2[1]
            l2[1]=party.replace('+',' ')
            dic1={'page':'1',l0[0]:l0[1],l1[0]:l1[1],l2[0]:l2[1]}
            page=1
        else:
            l0=l[0]
            l0=l0.split('=')
            l1=l[1]
            l1=l1.split('=')
            party=l1[1]
            l1[1]=party.replace('+',' ')
            l2=l[2]
            l2=l2.split('=')
            l3=l[3]
            l3=l3.split('=')
            party=l3[1]
            l3[1]=party.replace('+',' ')
            dic1={l0[0]:l0[1],l1[0]:l1[1],l2[0]:l2[1],l3[0]:l3[1]}
            page=l0[1]

    else:
        dic1={'page':'1','party_name':'','lot_no':'','quality':''}

    d=QueryDict('',mutable=True)
    d.update(dic1)

    print(d)

    if stateur== "ordergeneration":
        records_filter = ColorOrderFilter(d,queryset=records_list)
    elif stateur in ["goodsreceived","goodslease"]:
        records_filter = GodownLeaseFilter(d,queryset=records_list)
    else:
        records_filter = RecordFilter(d,queryset=records_list)

    # rows = Record.objects.filter(state="godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    for row in records_filter.qs:
        row_num += 1
        for col_num in range(len(row)):

            ws.write(row_num, col_num, str(row[col_num]), font_style)

    wb.save(response)

    return response




def export_all_xls(request):
    ur=request.META.get('HTTP_REFERER')
    ur=ur.split('?')
    stateur=ur[0]
    stateur=stateur.split('/')
    stateur=stateur[-1]
    if(stateur=="intransit"):
        file_name="Intransit-all"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Total Bale', 'Rate', 'LR No', 'Order No', 'State' ]
        records_list=Record.objects.filter(state="Transit").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'state')

    elif(stateur=="godown"):
        file_name="Godown-all"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'State' ]
        records_list=Record.objects.filter(state="Godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    elif(stateur=="checking"):
        file_name="Checked-all"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'Checking Date', 'State' ,'Checker name','Transport Agency']
        records_list=Record.objects.filter(state="Checked").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'lr_no', 'order_no', 'recieving_date', 'checking_date', 'state','checker__name','transport__transport')
    elif(stateur=="inprocess"):
        file_name="InProcess-all"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Checking Date', 'Sent to Processing Date', 'State', 'Processing Type', 'Processing Party' ]
        records_list=Record.objects.filter(state="In Process").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'checking_date', 'sent_to_processing_date', 'state', 'processing_type', 'agency_name__agency_name')
    elif(stateur=="readytoprint"):
        file_name="ProcessedGrey-all"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Sent to Processing Date', 'Processed Date', 'Processing Type', 'Arrival location', 'State' ]
        records_list=Record.objects.filter(state="Ready to print").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'sent_to_processing_date', 'recieve_processed_date', 'processing_type', 'arrival_location__location', 'state')

######color
    elif(stateur=="goodsreceived"):
        file_name="Godown Stock"
        columns=['chemical','quantity','unit','average rate(Rs)','godown name']
        godowns=ChemicalsGodownsMaster.objects.all()
        godowns_list=[]
        for g in godowns:
            godowns_list.append(g)
        records_list = ChemicalsGodownLooseMergeStock.objects.filter(state__in=godowns_list,loose_godown_state=None).exclude(quantity=0).values_list('color__color','quantity','unit__unit','rate','state__godown')



    elif(stateur=="goodslease"):
        file_name="Loose Godown Stock"
        columns=['chemical','quantity','unit','average rate(Rs)','loose godown name']
        lease=ChemicalsLooseGodownMaster.objects.all()
        lease_list=[]
        for g in lease:
            lease_list.append(g)
        records_list = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state__in=lease_list).values_list('color__color','quantity','unit__unit','rate','loose_godown_state__lease')
    else:
        file_name="Color Orders"
        columns = ['Supplier Name', 'order no', 'order Date', 'chemical', 'quantity', 'quantity remaining', 'unit', 'rate', 'order amount', 'Bill verify','state']
        records_list=ChemicalsAllOrders.objects.all().values_list('supplier__supplier', 'order_no', 'order_date', 'color__color', 'quantity', 'rem_quantity', 'unit__unit', 'rate', 'amount', 'validation', 'state')



    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s.xls'%file_name   #"Intransit-all.xls"

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Transit Data') # this will make a sheet named Users Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True


    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style) # at 0 row 0 column

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    #prev url req string to dict to querydict



    # rows = Record.objects.filter(state="godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    for row in records_list:
        row_num += 1
        for col_num in range(len(row)):

            ws.write(row_num, col_num, str(row[col_num]), font_style)

    wb.save(response)

    return response


###################################### RECORD DOWNLOAD END ###################################

############################# report print start ##############################
def export_report_xls(request):
    ur=request.META.get('HTTP_REFERER')
    ur=ur.split('?')
    stateur=ur[0]
    stateur=stateur.split('/')
    stateur=stateur[-1]
    if(stateur=="transportreport"):
        file_name="Transport-Report"
        columns = ['Lot no','Lr No','Sending Party','Quality', 'Bales Received','Rate(Rs)', 'Total Amount(Rs)']

        t_id=int(request.POST.get('transport'))
        transport=get_object_or_404(GreyTransportAgenciesMaster,id=t_id)
        begin = request.POST.get("start_date")
        end = request.POST.get("end_date")
        if(begin!="" or end!=""):

            begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
            end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
            selected_dates=[]

        # selected_qualities=[]
            next_day = begin
            while True:
                if next_day > end:
                    break
                selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
                next_day += datetime.timedelta(days=1)
        datalist=[]
        totalbales=0
        totaltotal=0

        recs=Record.objects.filter(transport=transport,checking_date__in=selected_dates).order_by('lot_no','checking_date')
        lot_list=[]
        for r in recs:
            if r.lot_no not in lot_list:
                lot_list.append(r.lot_no)

        for l in lot_list:
            rec_one = Record.objects.filter(lot_no=l,transport=transport,checking_date__in=selected_dates).first()
            than_inlot = rec_one.total_thans
            bale_inlot = rec_one.total_bale
            records=get_list_or_404(Record,lot_no=l,transport=transport,checking_date__in=selected_dates)
            than_recieved=0
            for r in records:
                than_recieved=than_recieved+r.than
            if than_inlot==than_recieved:
                row_list=[l,rec_one.lr_no,rec_one.party_name,rec_one.quality.qualities,bale_inlot,rec_one.transport.rate,round(rec_one.transport.rate*bale_inlot,2)]
                totalbales=totalbales+bale_inlot
                totaltotal=round(totaltotal + rec_one.transport.rate*bale_inlot,2)
                datalist.append(row_list)

            # datalist=[]

            # total=[]
            # totalthans=0
            # totaltotal=0
            # recs=Record.objects.filter(transport=transport,checking_date__in=selected_dates).order_by('lot_no','checking_date')
            # for r in recs:
            #     totalthans=totalthans+r.than

            #     l=[]
            #     l.append(r.lot_no)
            #     l.append(r.quality.qualities)
            #     l.append(str(r.checking_date))
            #     l.append(r.than)
            #     l.append(r.mtrs)
            #     mt=r.than
            #     # l.append(mt)
            #     try:
            #         # range=ThanRange.objects.filter(range1__lt=mt,range2__gt=mt).first()
            #         l.append(r.transport.rate)

            #         l.append(round((mt*r.transport.rate),2))
            #         totaltotal=totaltotal+round((mt*r.transport.rate),2)
            #     except:
            #         l.append("rate not defined")
            #         l.append("rate not defined")

            #     datalist.append(l)

    if(stateur=="checkerreport"):
        file_name="Checker-Report"
        columns = ['lot No','Quality', 'Checking Date', 'Thans Checked', 'Average cut', 'Rate(Rs)', 'Total(Rs)']
        #records_list=Record.objects.filter(state="Transit").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'state')
        c_id=int(request.POST.get('checker'))

        checker=get_object_or_404(Employee,id=c_id)
        begin = request.POST.get("start_date")
        end = request.POST.get("end_date")
        if(begin!="" or end!=""):

            begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
            end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
            selected_dates=[]

        # selected_qualities=[]
            next_day = begin
            while True:
                if next_day > end:
                    break
                selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
                next_day += datetime.timedelta(days=1)

            # qualities = Quality.objects.all()
            datalist=[]
            # for q in qualities:
            #     recs=Record.objects.filter(checker=checker,checking_date__in=selected_dates,quality=q.qualities)
            #     than=0
            #     mtrs=0
            total=[]
            totalthans=0
            totaltotal=0
            recs=Record.objects.filter(checker=checker,checking_date__in=selected_dates).order_by('quality','checking_date')
            for r in recs:
                totalthans=totalthans+r.than

                l=[]
                l.append(r.lot_no)
                l.append(r.quality.qualities)
                print(r.checking_date)
                l.append(str(r.checking_date))
                l.append(r.than)
                mt=round((r.mtrs/r.than),2)
                l.append(mt)
                try:
                    trange=GreyCheckingCutRatesMaster.objects.filter(range1__lt=mt,range2__gt=mt).first()
                    l.append(trange.rate)

                    l.append(round((mt*trange.rate),2))
                    totaltotal=totaltotal+round((mt*trange.rate),2)
                except:
                    l.append("rate not defined")
                    l.append("rate not defined")

                datalist.append(l)
    elif (stateur=="qualityreport"):
        file_name="Quality-Report"
        columns = ['Quality', 'Intransit Than', 'Intransit mtrs', 'Godown than', 'Godown mtrs', 'checked than','checked mtrs','In process than','In process mtrs','processed than','processed mtrs','total than','total mtrs']

        qual=(request.POST.get('qualities'))
        qualities=ast.literal_eval(qual)
        datalist=[]
        total_all=[]
        trthan=0
        trmtrs=0
        gothan=0
        gomtrs=0
        chthan=0
        chmtrs=0
        prthan=0
        prmtrs=0
        rethan=0
        remtrs=0
        tothan=0
        tomtrs=0
        for q in qualities:

        # if(request.POST.get(q.qualities)!=None):
        #     selected_qualities.append(request.POST.get(q.qualities))
            rec_transit=Record.objects.filter(state="Transit",quality=get_object_or_404(GreyQualitiesMaster,id=int(q)))
            tally_than=0
            tally_mtrs=0
            total_than_in_transit=0
            total_mtrs_in_transit=0

            for r in rec_transit:
                total_than_in_transit=total_than_in_transit+r.than
                total_mtrs_in_transit=total_mtrs_in_transit+r.mtrs
            trthan=trthan+total_than_in_transit
            trmtrs=trmtrs+total_mtrs_in_transit

            rec_godown=Record.objects.filter(state="Godown",quality=get_object_or_404(GreyQualitiesMaster,id=int(q)))
            total_than_in_godown=0
            total_mtrs_in_godown=0
            for r in rec_godown:
                total_than_in_godown=total_than_in_godown+r.than
                total_mtrs_in_godown=total_mtrs_in_godown+r.mtrs
            gothan=gothan+total_than_in_godown
            gomtrs=gomtrs+total_mtrs_in_godown

            rec_checked=Record.objects.filter(state="Checked",quality=get_object_or_404(GreyQualitiesMaster,id=int(q)))
            total_than_in_checked=0
            total_mtrs_in_checked=0
            for r in rec_checked:
                total_than_in_checked=total_than_in_checked+r.than
                total_mtrs_in_checked=total_mtrs_in_checked+r.mtrs
            chthan=chthan+total_than_in_checked
            chmtrs=chmtrs+total_mtrs_in_checked

            rec_process=Record.objects.filter(state="In Process",quality=get_object_or_404(GreyQualitiesMaster,id=int(q)))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            rec_ready=Record.objects.filter(state="Ready to print",quality=get_object_or_404(GreyQualitiesMaster,id=int(q)))
            total_than_in_ready=0
            total_mtrs_in_ready=0
            for r in rec_ready:
                total_than_in_ready=total_than_in_ready+r.than
                total_mtrs_in_ready=total_mtrs_in_ready+r.mtrs
            rethan=rethan+total_than_in_ready
            remtrs=remtrs+total_mtrs_in_ready

            tally_mtrs=total_mtrs_in_transit+total_mtrs_in_godown+total_mtrs_in_checked+total_mtrs_in_process+total_mtrs_in_ready
            tally_than=total_than_in_transit+total_than_in_godown+total_than_in_checked+total_than_in_process+total_than_in_ready

            tothan=tothan+tally_than
            tomtrs=tomtrs+tally_mtrs
            qual=get_object_or_404(GreyQualitiesMaster,id=int(q))
            d1=[qual.qualities,
            total_than_in_transit,round(total_mtrs_in_transit,2),
            total_than_in_godown,round(total_mtrs_in_godown,2),
            total_than_in_checked,round(total_mtrs_in_checked,2),
            total_than_in_process,round(total_mtrs_in_process,2),
            total_than_in_ready,round(total_mtrs_in_ready,2),
            tally_than,round(tally_mtrs,2)
            ]

            datalist.append(d1)
        total_all=["Total",
            round(trthan,2),round(trmtrs,2),
            round(gothan,2),round(gomtrs,2),
            round(chthan,2),round(chmtrs,2),
            round(prthan,2),round(prmtrs,2),
            round(rethan,2),round(remtrs,2),
            round(tothan,2),round(tomtrs,2),
        ]
        datalist.append(total_all)

    elif (stateur=="qualitypartyreport"):
        file_name="Quality-Report"
        columns = ['Quality','In process than','In process mtrs','processed than','processed mtrs','total than','total mtrs']

        qual=(request.POST.get('qualities'))
        qualities=ast.literal_eval(qual)

        begin = request.POST.get("start_date")
        end = request.POST.get("end_date")
        if(begin!="" or end!=""):

            begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
            end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
            selected_dates=[]

        # selected_qualities=[]
            next_day = begin
            while True:
                if next_day > end:
                    break
                selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
                next_day += datetime.timedelta(days=1)

        party_id=(request.POST.get('party'))
        party_ob=get_object_or_404(GreyOutprocessAgenciesMaster,agency_name=party_id)
        final_qs=[]
        total_all=[]

        prthan=0
        prmtrs=0
        rethan=0
        remtrs=0
        tothan=0
        tomtrs=0

        selected_qualities=[]
        for q in qualities:



            if(begin!="" or end!=""):
                rec_process=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="In Process",agency_name=party_ob,quality=get_object_or_404(GreyQualitiesMaster,id=int(q)))
            else:
                rec_process=Record.objects.filter(state="In Process",agency_name=party_ob,quality=get_object_or_404(GreyQualitiesMaster,id=int(q)))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            if(begin!="" or end!=""):
                rec_ready=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="Ready to print",agency_name=party_ob,quality=get_object_or_404(GreyQualitiesMaster,id=int(q)))
            else:
                rec_ready=Record.objects.filter(state="Ready to print",agency_name=party_ob,quality=get_object_or_404(GreyQualitiesMaster,id=int(q)))

            total_than_in_ready=0
            total_mtrs_in_ready=0
            for r in rec_ready:
                total_than_in_ready=total_than_in_ready+r.than
                total_mtrs_in_ready=total_mtrs_in_ready+r.mtrs
            rethan=rethan+total_than_in_ready
            remtrs=remtrs+total_mtrs_in_ready

            tally_mtrs=total_mtrs_in_process+total_mtrs_in_ready
            tally_than=total_than_in_process+total_than_in_ready

            tothan=tothan+tally_than
            tomtrs=tomtrs+tally_mtrs

            d1=[get_object_or_404(GreyQualitiesMaster,id=int(q)).qualities,
            total_than_in_process,round(total_mtrs_in_process,2),
            total_than_in_ready,round(total_mtrs_in_ready,2),
            tally_than,round(tally_mtrs,2)
            ]

            if(d1[1]==0 and d1[2]==0 and d1[3]==0 and d1[4]==0):
                pass
            else:
                final_qs.append(d1)
        total_all=["-",round(prthan,2),round(prmtrs,2),
            round(rethan,2),round(remtrs,2),
            round(tothan,2),round(tomtrs,2),
        ]
        final_qs.append(total_all)
        datalist=final_qs


    elif (stateur=="colorreport"):
        file_name="Color-Report"
        begin=request.POST.get('start_date')
        end=request.POST.get('end_date')
        columns = ['Color', 'unit', 'opening stock on %s'%str(begin), 'stock purchased', 'total stock', 'quantity Consumed/Moved','closing stock on %s'%str(end)]

        print(begin)

        begin = request.POST.get("start_date")
        end = request.POST.get("end_date")
        if(begin!="" or end!=""):

            begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
            end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
            selected_dates=[]

        # selected_qualities=[]
            next_day = begin
            while True:
                if next_day > end:
                    break



                selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
                next_day += datetime.timedelta(days=1)
        datalist=[]
        colors= Color.objects.all()
        units= ChemicalsUnitsMaster.objects.all()

        godowns = ChemicalsGodownsMaster.objects.all().order_by('godown')
        loose_godowns=ChemicalsLooseGodownMaster.objects.all().order_by('lease')

        selected_godowns_id = request.POST.get('selected_godowns')
        selected_godowns_id = ast.literal_eval(selected_godowns_id)

        selected_loose_id = request.POST.get('selected_loose')
        selected_loose_id = ast.literal_eval(selected_loose_id)

        selected_godowns=[]
        selected_loose=[]
        for g in selected_godowns_id:
            selected_godowns.append(get_object_or_404(ChemicalsGodownsMaster,id=int(g)))

        for g in selected_loose_id:
            selected_loose.append(get_object_or_404(ChemicalsLooseGodownMaster,id=int(g)))


        if selected_loose==[] and selected_godowns == []:
            for g in loose_godowns:
                selected_loose.append(g)
            for g in godowns:
                selected_godowns.append(g)

        # if selected_godowns == []:
        #     for g in godowns:
        #         selected_godowns.append(g)

        for c in colors:
            for u in units:
                try:
                    l=[]

        ######################### opening stock #########################################
                    try:
                        l.append(c.color)
                        l.append(u.unit)
                        quan=0
                        for g in selected_godowns:
                            first_record = ChemicalsClosingStockperGodown.objects.filter(dailydate__lt=selected_dates[0],color = c,unit = u,godown=g).order_by('-dailydate').first()
                            try:
                                quan=quan+first_record.quantity
                            except:
                                pass

                        for lg in selected_loose:
                            first_record = ChemicalsClosingStockperGodown.objects.filter(dailydate__lt=selected_dates[0],color = c,unit = u,loose_godown=lg).order_by('-dailydate').first()
                            try:
                                quan=quan+first_record.quantity
                            except:
                                pass

                        l.append(quan)
                    except:

                        l.append(0)

    ################################### new stock ##################################
                    new_stock=0
                    if selected_loose==[] and selected_godowns!=[]:
                        try:

                            #neworders = get_list_or_404(ColorRecord,recieving_date__in=selected_dates,color=c,unit=u)
                            neworders=ColorRecord.objects.filter(recieving_date__in=selected_dates,color=c,unit=u,godown__in=selected_godowns)

                            for i in neworders:

                                new_stock=new_stock+i.quantity

                        except:
                            pass
                    elif selected_godowns==[] and selected_loose!=[]:
                        try:
                            records=get_list_or_404(ChemicalsDailyConsumption,con_date__in=selected_dates,color=c,unit=u,loose_godown__in=selected_loose)


                            quantity = 0
                            for rec in records:
                                quantity = quantity+rec.quantity

                            consumed_stock=quantity

                        except:
                            consumed_stock=0
                        try:
                            q=0
                            for lg in selected_loose:
                                lstock = ChemicalsClosingStockperGodown.objects.filter(dailydate__lte=selected_dates[-1],color = c,unit = u,loose_godown=lg).order_by('-dailydate').first()
                                fstock = ChemicalsClosingStockperGodown.objects.filter(dailydate__lt=selected_dates[0],color = c,unit = u,loose_godown=lg).order_by('-dailydate').first()
                                print(fstock)
                                if fstock:

                                    q= q+lstock.quantity - fstock.quantity
                                else:
                                    q=q+lstock.quantity

                            new_stock=q+consumed_stock
                        except:
                            pass


                    else:
                        try:

                            #neworders = get_list_or_404(ColorRecord,recieving_date__in=selected_dates,color=c,unit=u)
                            neworders=ColorRecord.objects.filter(recieving_date__in=selected_dates,color=c,unit=u,godown__in=selected_godowns)

                            for i in neworders:

                                new_stock=new_stock+i.quantity

                        except:
                            pass
                    l.append(new_stock)

#################### total stock #################################
                    x=l[2]+l[3]
                    l.append(round(x,2))

####################### closing stock calculations ##############################

                    try:
                        lquan=0
                        for g in selected_godowns:
                            last_record = ChemicalsClosingStockperGodown.objects.filter(dailydate__lte=selected_dates[-1],color = c,unit = u,godown=g).order_by('-dailydate').first()
                            try:
                                lquan=lquan+last_record.quantity
                            except:
                                pass
                        for s in selected_loose:
                            last_record1 = ChemicalsClosingStockperGodown.objects.filter(dailydate__lte=selected_dates[-1],color = c,unit = u,loose_godown=s).order_by('-dailydate').first()
                            try:
                                lquan=lquan+last_record1.quantity
                            except:
                                pass
                    except:
                        pass

    ######################### daily consumption ####################################
                    if selected_godowns!=[] and selected_loose==[]:
                        x=l[2]+l[3]-lquan
                        l.append(round(x,2))
                    elif selected_loose!=[] and selected_godowns==[]:
                        try:
                            records=get_list_or_404(ChemicalsDailyConsumption,con_date__in=selected_dates,color=c,unit=u,loose_godown__in=selected_loose)


                            quantity = 0
                            for rec in records:
                                quantity = quantity+rec.quantity

                            l.append(quantity)
                        except:
                            l.append(0)
                    else:
                        try:
                            records=get_list_or_404(ChemicalsDailyConsumption,con_date__in=selected_dates,color=c,unit=u,loose_godown__in=selected_loose)


                            quantity = 0
                            for rec in records:
                                quantity = quantity+rec.quantity

                            l.append(quantity)
                        except:
                            l.append(0)
    ####################################### closing stock #########################################
                    try:
                        lquan=0
                        for g in selected_godowns:
                            last_record = ChemicalsClosingStockperGodown.objects.filter(dailydate__lte=selected_dates[-1],color = c,unit = u,godown=g).order_by('-dailydate').first()
                            try:
                                lquan=lquan+last_record.quantity
                            except:
                                pass
                        for s in selected_loose:
                            last_record1 = ChemicalsClosingStockperGodown.objects.filter(dailydate__lte=selected_dates[-1],color = c,unit = u,loose_godown=s).order_by('-dailydate').first()
                            try:
                                lquan=lquan+last_record1.quantity
                            except:
                                pass
                    except:
                        pass


                    l.append(lquan)

                    if l[2]==0 and l[3]==0 and l[5]==0:
                        pass
                    else:
                        datalist.append(l)
                    # print(first_record.quantity,first_record.con_date)
                except:
                    pass

    #     begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
    #     end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
    #     selected_dates=[]

    # # selected_qualities=[]
    #     next_day = begin
    #     while True:
    #         if next_day > end:
    #             break



    #         selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
    #         next_day += datetime.timedelta(days=1)
    #     datalist=[]
    #     colors= Color.objects.all()
    #     units= ChemicalsUnitsMaster.objects.all()
    #     for c in colors:
    #         for u in units:
    #             try:
    #                 l=[]
    #                 try:
    #                     first_record = ChemicalsClosingStock.objects.filter(dailydate__lt=selected_dates[0],color = c,unit = u).order_by('-dailydate').first()
    #                     l.append(c.color)
    #                     l.append(u.unit)
    #                     l.append(first_record.quantity)
    #                 except:

    #                     l.append(0)

    #                 new_stock=0
    #                 try:
    #                     neworders = get_list_or_404(ColorRecord,recieving_date__in=selected_dates,color=c,unit=u)
    #                     for i in neworders:
    #                         new_stock=new_stock+i.quantity
    #                 except:
    #                     pass

    #                 l.append(new_stock)
    #                 l.append(new_stock+l[-1])
    #                 try:
    #                     last_record = get_object_or_404(ChemicalsClosingStock,dailydate=selected_dates[-1],color = c,unit = u)
    #                 except:
    #                     last_record = ChemicalsClosingStock.objects.filter(dailydate__lt=selected_dates[-1],color = c,unit = u).order_by('-dailydate').first()


    #                 try:
    #                     records=get_list_or_404(ChemicalsDailyConsumption,con_date__in=selected_dates,color=c,unit=u)


    #                     quantity = 0
    #                     for rec in records:
    #                         quantity = quantity+rec.quantity

    #                     l.append(quantity)
    #                 except:
    #                     l.append(0)

    #                 l.append(last_record.quantity)
    #                 # new_stock=(l[4]-l[3])
    #                 # if(new_stock>0):
    #                 #     l.append(new_stock)

    #                 datalist.append(l)
    #                 # print(first_record.quantity,first_record.con_date)
    #             except:
    #                 pass

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s.xls'%file_name   #"Intransit-all.xls"

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('report') # this will make a sheet named Users Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True


    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style) # at 0 row 0 column

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    for row in datalist:
        row_num += 1
        for col_num in range(len(row)):

            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)

    return response

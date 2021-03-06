from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,GreyQualityMaster,GreyCheckingCutRatesMaster,GreyOutprocessAgenciesMaster,GreyGodownsMaster, GreyTransportAgenciesMaster, GreySuppliersMaster, Employee, GreyOrders, OrderStatus, LotStatus, GreyLots
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

###### GREY MODULE ######


def greyhome(request):
    return render(request, './GreyModule/GreyHome/greyHome.html')

def greylots(request):
    return redirect('/lotList')

###### BACK BUTTONS ######
def back1(request):
    return redirect('/intransit')

def back2checking(request):
    return redirect('/checking')

def back(request,state):
    print(state)
    if state == "Transit":
        return redirect('/intransit')
    elif state == "Godown":
        return redirect('/godown')
    elif state == "Checked":
        return redirect('/checking')
    elif state == "In Process":
        return redirect('/inprocess')
    elif state == "Ordered" or state == "In Transit":
        return redirect('/ordergeneration')

def backtoorders(request,state):
    godowns=ChemicalsGodownsMaster.objects.all()

    g_list=[]

    for g in godowns:
        g_list.append(g.godown)
    lease=ChemicalsLooseGodownMaster.objects.all()

    l_list=[]

    for g in lease:
        l_list.append(g.lease)

    if state == "Ordered" or state == "In Transit" or state == "Godown":
        return redirect('/ordergeneration')
    elif state in g_list:
        return redirect('/goodsreceived')
    elif state in l_list:
        return redirect('/goodslease')

###### GREY UPLOAD EXCEL SHEET ######
def upload(request):
    counter = 0
    if request.method == 'POST':
        item_resource = ItemResources()
        dataset = Dataset()
        try:
            new_item = request.FILES['myfile']
            excel_data_df = pandas.read_excel(new_item, skiprows=[0,1,2,3,4,5])
            excel_data_df.rename(columns = {'Unnamed: 0':'sr_no','Party Name':'party_name', 'Bill No':'bill_no', 'Bill Date':'bill_date', 'Bill Amt':'bill_amount','Unnamed: 7':'Lot Number', 'Quality':'quality', 'Than':'than', 'Mtrs':'mtrs', 'Bale':'bale', 'Rate':'rate', 'Unnamed: 14':'lr_no', 'Order No':'order_no',}, inplace = True)
            excel_data_df.drop(['S.No', 'Lot No', 'LR No'],axis=1, inplace = True)
            excel_data_df['sr_no'].replace('', np.nan, inplace=True)

            excel_data_df.dropna(subset=['sr_no'], inplace=True)
            empty_cols = [col for col in excel_data_df.columns if excel_data_df[col].isnull().all()]
            # Drop these columns from the dataframe
            excel_data_df.drop(empty_cols,axis=1,inplace=True)
            excel_data_df['quality'] = excel_data_df['quality'].apply(lambda x: x.replace('"', 'inch'))
            imported_data = dataset.load(excel_data_df)
            # result = item_resource.import_data(dataset, dry_run=True)
            # print(imported_data)
        except:
            messages.error(request, "Please Select Proper File")
            return redirect('/greyhome')

        for data in imported_data:
            try:
                q_object=get_object_or_404(GreyQualityMaster,
                    quality_name=data[6])
            except:
                q_object = GreyQualityMaster(
                    quality_name=data[6]
                    )
                q_object.save()
            quality_object=get_object_or_404(GreyQualityMaster,quality_name=data[6])
            try:

                rec=get_list_or_404(Record,
                    party_name=data[1],
                    bill_no=data[2],
                    lot_no=data[5],
                    lr_no=data[11],
                    order_no=data[12])
            except:
                d=str(data[3])
                value = Record(
                    sr_no=data[0],
                    party_name=data[1],
                    bill_no=data[2],
                    bill_date=datetime.datetime.strptime(d[0:10], '%Y-%m-%d').strftime('%b %d,%Y'),#(data[3]).date(),
                    bill_amount=data[4],
                    lot_no=data[5],
                    quality=quality_object,
                    than=data[7],
                    mtrs=data[8],
                    bale=data[9],
                    rate=data[10],
                    lr_no=data[11],
                    order_no=data[12],
                    total_bale=data[9],
                    total_thans=data[7],
                    total_mtrs=data[8]

                    )
                value.save()
                counter = counter + 1

        if (counter > 0):
            messages.success(request,str(counter)+ " Records were Inserted")
        else:
            messages.error(request, "These records already exist")


    return redirect('/greyhome')

###### GREY - INTRANSIT STOCK ######
def showIntransit(request):
    records_list=Record.objects.filter(state="Transit").order_by('lot_no')

    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    sum_amount = 0
    sum_than = 0
    sum_bale = 0
    sum_mtrs = 0
    for i in records:
        sum_amount=sum_amount+i.bill_amount
        sum_bale=sum_bale+i.bale
        sum_than=sum_than+i.than
        sum_mtrs=sum_mtrs+i.mtrs
    sums=[round(sum_amount,2),sum_than,round(sum_mtrs,2),sum_bale]
    quality_name=GreyQualityMaster.objects.all().order_by('quality_name')

    return render(request, './GreyModule/intransit.html',{'records':records,'filter':records_filter,'sums':sums,'quality_name':quality_name})

###### GREY - GODOWN STOCK ######
def showGodown(request):
    records_list=Record.objects.filter(state="Godown").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    sum_amount = 0
    sum_than = 0
    sum_bale = 0
    sum_mtrs = 0
    for i in records:
        sum_amount=sum_amount+i.bill_amount
        sum_bale=sum_bale+i.bale
        sum_than=sum_than+i.than
        sum_mtrs=sum_mtrs+i.mtrs
    sums=[round(sum_amount,2),sum_than,round(sum_mtrs,2),sum_bale]
    quality_name=GreyQualityMaster.objects.all().order_by('quality_name')
    return render(request, './GreyModule/godown.html',{'records':records,'filter':records_filter,'sums':sums,'quality_name':quality_name})

###### GREY - REQUEST GODOWN STOCK ######
def showGodownRequest(request):
    records_list=Record.objects.filter(state="Transit").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, './GreyModule/godownrequest.html',{'records':records,'filter':records_filter})

###### Edit form for intransit record ######
def record(request,id):
    rec=get_object_or_404(Record, id=id)
    quality_name=GreyQualityMaster.objects.all().order_by('quality_name')
    return render(request, './GreyModule/record.html', {'record':rec,'quality_name':quality_name})

###### GODOWN APPROVE FORM ######
def goDownApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    mindate=datetime.datetime.strptime(rec.bill_date,'%b %d,%Y').strftime('%Y-%m-%d')
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    quality_name = GreyQualityMaster.objects.all()
    d=datetime.date.today()
    d=str(d)
    return render(request, './GreyModule/godownapprove.html', {'record':rec,'quality_name':quality_name,'mindate':mindate,'maxdate':maxdate,'date':d})

 ###### Edit in transit record ######
def edit(request,id):
    if request.method=="POST":
        record = get_object_or_404(Record,id=id)
        prevBale=record.bale
        record.party_name=request.POST.get("party_name")
        record.bill_no=request.POST.get("bill_no")
        record.bill_date=request.POST.get("bill_date")
        record.bill_amount=request.POST.get("bill_amount")
        record.lot_no=request.POST.get("lot_no")
        q_id=request.POST.get("quality")
        quality_ob=get_object_or_404(GreyQualityMaster,id=int(q_id))
        record.quality=quality_ob
        record.than=request.POST.get("than")
        record.mtrs=request.POST.get("mtrs")
        record.bale=request.POST.get("bale")
        record.rate=request.POST.get("rate")
        record.lr_no=request.POST.get("lr_no")
        record.order_no=request.POST.get("order_no")
        if prevBale == record.total_bale:
            record.total_bale=request.POST.get("bale")
            record.total_thans=request.POST.get("than")
            record.total_mtrs=request.POST.get("mtrs")
        else:
            messages.error(request,"Half of the goods have already advanced, so total bales cannot be updated")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        if len(request.POST.get("party_name"))<1 or len(str(request.POST.get("bill_no")))<1 or len(str(request.POST.get("bill_amount")))<1 or len(request.POST.get("quality"))<1 or len(str(request.POST.get("than")))<1 or len(str(request.POST.get("mtrs")))<1 or len(str(request.POST.get("bale")))<1 or len(str(request.POST.get("rate")))<1 or len(str(request.POST.get("lr_no")))<1 or len(str(request.POST.get("order_no")))<1:
            messages.error(request,"Field Cannot be EMPTY")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            record.save()
            messages.success(request,"Data Updated Successfully")
        #print(record.bill_date)
        return redirect('/intransit')


##### NEXT AND PREVIOUS BUTTONS #####
def nextRec(request,id):
    rec=get_object_or_404(Record, id=id+1)
    return render(request, './GreyModule/record.html', {'record':rec})

def prevRec(request,id):
    rec=get_object_or_404(Record, id=id-1)
    return render(request, './GreyModule/record.html', {'record':rec})

##### Intransit To Godown #####
def approveBale(request,id):
    prevRec = get_object_or_404(Record,id=id)
    bale_recieved=request.POST.get("bale_recieved")
    bale_recieved = int(bale_recieved)

    total_amount=prevRec.bill_amount
    totalthan=prevRec.than
    cost_per_than=total_amount/totalthan
    cost_per_than=round(cost_per_than,2)
    if(prevRec.bale == bale_recieved):
        prevRec.state="Godown"
        prevRec.recieving_date=str(request.POST["recieving_date"])
        prevRec.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/intransit')
    elif(prevRec.bale<bale_recieved):
        messages.error(request,"Bale Recieved cannot be more than Original Amount of Bale")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        bale_in_transit = prevRec.bale - bale_recieved

        than_in_transit = prevRec.than/prevRec.bale
        than_in_transit = than_in_transit * bale_in_transit
        than_in_godown = prevRec.than - than_in_transit

        mtrs_in_transit = prevRec.mtrs/prevRec.bale
        mtrs_in_transit = mtrs_in_transit * bale_in_transit
        mtrs_in_transit = round(mtrs_in_transit,2)
        mtrs_in_godown = prevRec.mtrs - mtrs_in_transit
        mtrs_in_godown = round(mtrs_in_godown,2)


        value = Record(
            sr_no=prevRec.sr_no,
            party_name=prevRec.party_name,
            bill_no=prevRec.bill_no,
            bill_date=prevRec.bill_date,
            bill_amount=round(than_in_godown * cost_per_than,2),
            lot_no=prevRec.lot_no,
            quality=prevRec.quality,
            than=than_in_godown,
            mtrs=mtrs_in_godown,
            bale=bale_recieved,
            rate=prevRec.rate,
            lr_no=prevRec.lr_no,
            order_no=prevRec.order_no,
            state="Godown",
            recieving_date = str(request.POST["recieving_date"]),
            total_bale=prevRec.total_bale,
            total_thans=prevRec.total_thans,
            total_mtrs=prevRec.total_mtrs
            )

        if bale_recieved == 0 :
            messages.error(request,"Bale Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            value.save()
            prevRec.bale = bale_in_transit
            prevRec.than = than_in_transit
            prevRec.mtrs = mtrs_in_transit
            prevRec.bill_amount = round(than_in_transit * cost_per_than,2)
            prevRec.save()
            messages.success(request,"Data Updated Successfully")
        #print(than_in_transit,than_in_godown)
        return redirect('/intransit')

#quality2 = request.POST.get("quality2")

############ GREY: CHECKING OF STOCKS START #################
def showChecked(request):
    records_list=Record.objects.filter(state="Checked").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    sum_amount = 0
    sum_than = 0
    sum_mtrs = 0
    for i in records:
        sum_amount=sum_amount+i.bill_amount
        sum_than=sum_than+i.than
        sum_mtrs=sum_mtrs+i.mtrs
    sums=[round(sum_amount,2),sum_than,round(sum_mtrs,2)]
    quality_name=GreyQualityMaster.objects.all().order_by('quality_name')
    return render(request, './GreyModule/Checking.html',{'records':records,'filter':records_filter,'sums':sums,'quality_name':quality_name})

def showCheckingRequest(request):
    records_list=Record.objects.filter(state="Godown").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, './GreyModule/CheckingRequest',{'records':records,'filter':records_filter})

def checkingApprove(request,id):
    rec=get_object_or_404(Record, id=id)

    mindate=str(rec.recieving_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    quality_all = GreyQualityMaster.objects.all().order_by('quality_name')
    checkers=Employee.objects.all().order_by('name')
    transports=GreyTransportAgenciesMaster.objects.all().order_by('transport_agency')
    d=datetime.date.today()
    d=str(d)
    return render(request, './GreyModule/checkingApprove.html', {'date':d,'record':rec,'transport_agency':transports,'checkers':checkers,'quality_name':quality_all,'mindate':mindate,'maxdate':maxdate})

def approveCheck(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_recieved")
    than_recieved = int(than_recieved)
    defect=request.POST.get("defect")
    mtrs_edit=request.POST.get("mtrs-checked")

    checker_id=int(request.POST.get("checker"))
    checker=get_object_or_404(Employee,id=checker_id)
    t=int(request.POST.get("transport_agency"))
    transport_agency=get_object_or_404(GreyTransportAgenciesMaster,id=t)

    q_id=int(request.POST.get("new-quality"))
    quality_object=get_object_or_404(GreyQualityMaster,id=q_id)

    total_amount=prevRec.bill_amount
    totalthan=prevRec.than
    cost_per_than=total_amount/totalthan
    cost_per_than=round(cost_per_than,2)
    if(defect=="no defect"):

        if(prevRec.than == than_recieved):
            prevRec.state="Checked"
            prevRec.quality=quality_object
            prevRec.checking_date=str(request.POST["checking_date"])
            prevRec.checker=checker
            prevRec.transport_agency=transport_agency

            if(mtrs_edit==""):
                mtrs_edit=prevRec.mtrs
            prevRec.mtrs=mtrs_edit
            prevRec.save()
            messages.success(request,"Data Updated Successfully")
            return redirect('/godown')
        elif(prevRec.than<than_recieved):
            messages.error(request,"Than Recieved cannot be more than Original Amount of Than")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            than_un_checked = prevRec.than - than_recieved

            bale_per_than = prevRec.bale/prevRec.than
            bale_un_checked = than_un_checked * bale_per_than
            bale_checked = prevRec.bale - bale_un_checked

            mtrs_un_checked = prevRec.mtrs/prevRec.than
            mtrs_un_checked = mtrs_un_checked * than_un_checked
            mtrs_un_checked = round(mtrs_un_checked,2)
            if(mtrs_edit==""):
                print(mtrs_edit)
                mtrs_checked = prevRec.mtrs - mtrs_un_checked
                mtrs_checked = round(mtrs_checked,2)
            else:
                print(type(mtrs_edit))
                mtrs_checked=mtrs_edit

            value = Record(
                sr_no=prevRec.sr_no,
                party_name=prevRec.party_name,
                bill_no=prevRec.bill_no,
                bill_date=prevRec.bill_date,
                bill_amount=round(cost_per_than * than_recieved,2),
                lot_no=prevRec.lot_no,
                quality=quality_object,
                than=than_recieved,
                mtrs=mtrs_checked,
                bale=bale_checked,
                rate=prevRec.rate,
                lr_no=prevRec.lr_no,
                order_no=prevRec.order_no,
                state="Checked",
                recieving_date =prevRec.recieving_date,
                total_bale=prevRec.total_bale,
                total_mtrs=prevRec.total_mtrs,
                total_thans=prevRec.total_thans,
                checking_date=str(request.POST["checking_date"]),
                checker=checker,
                transport_agency=transport_agency

                )
            if than_recieved == 0 :
                messages.error(request,"Than Recieved cannot be Zero (0)")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                value.save()
                prevRec.bale = bale_un_checked
                prevRec.than = than_un_checked
                prevRec.mtrs = mtrs_un_checked
                prevRec.bill_amount = round(cost_per_than * than_un_checked,2)
                prevRec.save()
                messages.success(request,"Data Updated Successfully")

    else:
        if(prevRec.than == than_recieved):
            prevRec.state=request.POST.get("defect")
            prevRec.quality=quality_object
            prevRec.checking_date=str(request.POST["checking_date"])
            prevRec.checker=checker
            prevRec.transport_agency=transport_agency
            if(mtrs_edit==""):
                mtrs_edit=prevRec.mtrs
            prevRec.mtrs=mtrs_edit
            prevRec.save()
            messages.success(request,"Data updated to defective state")

            return redirect('/godown')
        elif(prevRec.than<than_recieved):
            messages.error(request,"Than Recieved cannot be more than Original Amount of Than")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        else:
            than_un_checked = prevRec.than - than_recieved

            bale_per_than = prevRec.bale/prevRec.than
            bale_un_checked = than_un_checked * bale_per_than
            bale_checked = prevRec.bale - bale_un_checked

            mtrs_un_checked = prevRec.mtrs/prevRec.than
            mtrs_un_checked = mtrs_un_checked * than_un_checked
            mtrs_un_checked = round(mtrs_un_checked,2)
            if(mtrs_edit==""):
                print(mtrs_edit)
                mtrs_checked = prevRec.mtrs - mtrs_un_checked
                mtrs_checked = round(mtrs_checked,2)
            else:
                print(type(mtrs_edit))
                mtrs_checked=mtrs_edit

            value = Record(
                sr_no=prevRec.sr_no,
                party_name=prevRec.party_name,
                bill_no=prevRec.bill_no,
                bill_date=prevRec.bill_date,
                bill_amount=round(cost_per_than * than_recieved,2),
                lot_no=prevRec.lot_no,
                quality=quality_object,
                than=than_recieved,
                mtrs=mtrs_checked,
                bale=bale_checked,
                rate=prevRec.rate,
                lr_no=prevRec.lr_no,
                order_no=prevRec.order_no,
                state=request.POST.get("defect"),
                recieving_date =prevRec.recieving_date,
                total_bale=prevRec.total_bale,
                total_mtrs=prevRec.total_mtrs,
                total_thans=prevRec.total_thans,
                checking_date=str(request.POST["checking_date"]),
                checker=checker,
                transport_agency=transport_agency

                )
            if than_recieved == 0 :
                messages.error(request,"Than Recieved cannot be Zero (0)")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                value.save()
                prevRec.bale = bale_un_checked
                prevRec.than = than_un_checked
                prevRec.mtrs = mtrs_un_checked
                prevRec.bill_amount = round(cost_per_than * than_un_checked,2)
                prevRec.save()
                messages.success(request,"Data updated to defective state")

    return redirect('/godown')

##### FUNCTION TO SEND STOCK BACK TO PREVIOUS STATE #####
def changeStateBack(request,id):
    rec=get_object_or_404(Record,id=id)
    if rec.state=="Checked":
        rec.state="Godown"
        rec.save()
        return redirect('/checking')
    elif rec.state=="In Process":
        rec.state="Checked"
        rec.save()
        return redirect('/inprocess')
    else:
        rec.state="In Process"
        rec.save()
        return redirect('/readytoprint')

def editChecked(request,id):
    rec=get_object_or_404(Record, id=id)
    return render(request, './GreyModule/editchecked.html', {'record':rec})

def checkedEdit(request,id):
    if request.method=="POST":
        record = get_object_or_404(Record,id=id)
        record.party_name=request.POST.get("party_name")
        record.bill_no=request.POST.get("bill_no")
        record.bill_date=request.POST.get("bill_date")
        record.bill_amount=request.POST.get("bill_amount")
        record.lot_no=request.POST.get("lot_no")
        # record.quality=request.POST.get("quality")
        record.than=request.POST.get("than")
        record.mtrs=request.POST.get("mtrs")
        record.bale=request.POST.get("bale")
        record.rate=request.POST.get("rate")
        record.lr_no=request.POST.get("lr_no")
        record.order_no=request.POST.get("order_no")
        if len(request.POST.get("party_name"))<1 or len(str(request.POST.get("bill_no")))<1 or len(str(request.POST.get("bill_amount")))<1 or len(request.POST.get("quality"))<1 or len(str(request.POST.get("than")))<1 or len(str(request.POST.get("mtrs")))<1 or len(str(request.POST.get("bale")))<1 or len(str(request.POST.get("rate")))<1 or len(str(request.POST.get("lr_no")))<1 or len(str(request.POST.get("order_no")))<1:
            messages.error(request,"Field Cannot be EMPTY")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            record.save()
            messages.success(request,"Data Updated Successfully")
        #print(record.bill_date)
        return redirect('/checking')
############ GREY: CHECKING OF STOCKS END #################


####### GREY - PROCESSING #######
####### GREY - Stock in Processing #######
def showProcessing(request):
    records_list=Record.objects.filter(state="In Process").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    sum_amount = 0
    sum_than = 0
    sum_mtrs = 0
    for i in records:
        sum_amount=sum_amount+i.bill_amount
        sum_than=sum_than+i.than
        sum_mtrs=sum_mtrs+i.mtrs
    sums=[round(sum_amount,2),sum_than,round(sum_mtrs,2)]
    quality_name=GreyQualityMaster.objects.all().order_by('quality_name')
    return render(request, './GreyModule/processing.html',{'records':records,'filter':records_filter,'sums':sums,'quality_name':quality_name})

def showProcessingRequest(request):
    records_list=Record.objects.filter(state="Checked").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, './GreyModule/processingrequest.html',{'records':records,'filter':records_filter})

def processingApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    mindate=str(rec.checking_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    processing_parties = GreyOutprocessAgenciesMaster.objects.all().order_by('agency_name')
    d=datetime.date.today()
    d=str(d)
    return render(request, './GreyModule/processingapprove.html', {'date':d,'record':rec,'parties':processing_parties,'mindate':mindate,'maxdate':maxdate})

def sendInProcess(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_to_process")
    than_recieved = int(than_recieved)
    process_type = request.POST.get("processing-type")
    party_id=int(request.POST.get("processing-party"))
    partyprocessing=get_object_or_404(GreyOutprocessAgenciesMaster,id=party_id)
    total_amount=prevRec.bill_amount
    totalthan=prevRec.than
    cost_per_than=total_amount/totalthan
    cost_per_than=round(cost_per_than,2)
    if(prevRec.than == than_recieved):
        prevRec.state="In Process"
        prevRec.agency_name=partyprocessing
        prevRec.sent_to_processing_date=str(request.POST["sending_date"])
        prevRec.processing_type = process_type
        prevRec.gate_pass = int(request.POST.get('gatepass'))
        prevRec.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/checking')
    elif(prevRec.than<than_recieved):
        messages.error(request,"Than Recieved cannot be more than Original Amount of Than")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        than_un_checked = prevRec.than - than_recieved

        bale_per_than = prevRec.bale/prevRec.than
        bale_un_checked = than_un_checked * bale_per_than
        bale_checked = prevRec.bale - bale_un_checked

        mtrs_un_checked = prevRec.mtrs/prevRec.than
        mtrs_un_checked = mtrs_un_checked * than_un_checked
        mtrs_un_checked = round(mtrs_un_checked,2)
        mtrs_checked = prevRec.mtrs - mtrs_un_checked
        mtrs_checked = round(mtrs_checked,2)


        value = Record(
            sr_no=prevRec.sr_no,
            party_name=prevRec.party_name,
            bill_no=prevRec.bill_no,
            bill_date=prevRec.bill_date,
            bill_amount=round(cost_per_than * than_recieved,2),
            lot_no=prevRec.lot_no,
            quality=prevRec.quality,
            than=than_recieved,
            mtrs=mtrs_checked,
            bale=bale_checked,
            rate=prevRec.rate,
            lr_no=prevRec.lr_no,
            order_no=prevRec.order_no,
            state="In Process",
            recieving_date =prevRec.recieving_date,
            total_bale=prevRec.total_bale,
            agency_name = partyprocessing,
            processing_type = process_type,
            checking_date = prevRec.checking_date,
            sent_to_processing_date=str(request.POST["sending_date"]),
            total_thans=prevRec.total_thans,
            total_mtrs=prevRec.total_mtrs,
            gate_pass = int(request.POST.get('gatepass')),
            checker=prevRec.checker,
            transport_agency=prevRec.transport_agency

            )
        if than_recieved == 0 :
            messages.error(request,"Than Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            value.save()
            prevRec.bale = bale_un_checked
            prevRec.than = than_un_checked
            prevRec.mtrs = mtrs_un_checked
            prevRec.bill_amount = round(cost_per_than * than_un_checked,2)
            prevRec.save()
            messages.success(request,"Data Updated Successfully")
        #print(than_in_transit,than_in_godown)
        return redirect('/checking')

####### GREY - PROCESSING END #######

####### GREY - READY TO PRINT #######
####### GREY - READY TO PRINT STOCK #######
def showReadyToPrint(request):
    records_list=Record.objects.filter(state="Ready to print").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    sum_amount = 0
    sum_than = 0
    sum_mtrs = 0
    for i in records:
        sum_amount=sum_amount+i.bill_amount
        sum_than=sum_than+i.than
        sum_mtrs=sum_mtrs+i.mtrs
    sums=[round(sum_amount,2),sum_than,round(sum_mtrs,2)]
    quality_name=GreyQualityMaster.objects.all().order_by('quality_name')
    return render(request, './GreyModule/readytoprint.html',{'records':records,'filter':records_filter,'sums':sums,'quality_name':quality_name})

def showReadyRequest(request):
    records_list=Record.objects.filter(state="In Process").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, './GreyModule/readytoprintrequest.html',{'records':records,'filter':records_filter})

def readyApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    mindate=str(rec.sent_to_processing_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    locations = GreyGodownsMaster.objects.all().order_by('godown_name')

    d=datetime.date.today()
    d=str(d)
    return render(request, './GreyModule/readypprove.html', {'date':d,'record':rec,'mindate':mindate,'maxdate':maxdate,'parties':locations})

def readyToPrint(request,id):
    prevRec = get_object_or_404(Record,id=id)
    loc_id = int(request.POST.get("arrival-location"))
    location = get_object_or_404(GreyGodownsMaster,id=loc_id)
    tally_lot_no = prevRec.lot_no
    tally_total_thans=prevRec.total_thans
    than_recieved=request.POST.get("than_ready")
    than_recieved = int(than_recieved)

    total_amount=prevRec.bill_amount
    totalthan=prevRec.than
    cost_per_than=total_amount/totalthan
    cost_per_than=round(cost_per_than,2)
    if(prevRec.than == than_recieved):
        prevRec.state="Ready to print"
        prevRec.recieve_processed_date=str(request.POST.get("processing_date"))
        prevRec.godown_name = location
        prevRec.chalan_no = int(request.POST.get('chalan'))
        prevRec.save()
        tally_records = Record.objects.filter(state="Ready to print",lot_no=tally_lot_no)
        tally_thans=0
        for tr in tally_records:
            tally_thans=tally_thans+tr.than
        if (tally_thans==tally_total_thans):
            for tr in tally_records:
                tr.tally=True
                tr.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/inprocess')
    elif(prevRec.than<than_recieved):
        messages.error(request,"Than Recieved cannot be more than Original Amount of Than")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        than_un_checked = prevRec.than - than_recieved

        bale_per_than = prevRec.bale/prevRec.than
        bale_un_checked = than_un_checked * bale_per_than
        bale_checked = prevRec.bale - bale_un_checked

        mtrs_un_checked = prevRec.mtrs/prevRec.than
        mtrs_un_checked = mtrs_un_checked * than_un_checked
        mtrs_un_checked = round(mtrs_un_checked,2)
        mtrs_checked = prevRec.mtrs - mtrs_un_checked
        mtrs_checked = round(mtrs_checked,2)


        value = Record(
            sr_no=prevRec.sr_no,
            party_name=prevRec.party_name,
            bill_no=prevRec.bill_no,
            bill_date=prevRec.bill_date,
            bill_amount=round(cost_per_than * than_recieved,2),
            lot_no=prevRec.lot_no,
            quality=prevRec.quality,
            than=than_recieved,
            mtrs=mtrs_checked,
            bale=bale_checked,
            rate=prevRec.rate,
            lr_no=prevRec.lr_no,
            order_no=prevRec.order_no,
            state="Ready to print",
            recieving_date =prevRec.recieving_date,
            total_bale=prevRec.total_bale,
            agency_name = prevRec.agency_name,
            sent_to_processing_date = prevRec.sent_to_processing_date,
            recieve_processed_date=str(request.POST.get("processing_date")),
            total_mtrs=prevRec.total_mtrs,
            total_thans=prevRec.total_thans,
            godown_name=location,
            processing_type=prevRec.processing_type,
            gate_pass=prevRec.gate_pass,
            chalan_no = int(request.POST.get('chalan')),
            checker=prevRec.checker,
            transport_agency=prevRec.transport_agency,
            checking_date=prevRec.checking_date,
            )
        if than_recieved == 0 :
            messages.error(request,"Than Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            value.save()
            prevRec.bale = bale_un_checked
            prevRec.than = than_un_checked
            prevRec.mtrs = mtrs_un_checked
            prevRec.bill_amount = round(cost_per_than * than_un_checked,2)
            prevRec.save()
            messages.success(request,"Data Updated Successfully")


        #print(than_in_transit,than_in_godown)
        return redirect('/inprocess')

####### GREY - READY TO PRINT END #######

########################################## GREY REPORTING #################################################################

############### GREY - LEDGER REPORT #################
def reportFilter(request):
    processing_parties = GreyOutprocessAgenciesMaster.objects.all().order_by('agency_name')
    partyname =[]
    records = Record.objects.all().order_by('party_name')
    d=str(datetime.date.today())
    for rec in records:
        if(rec.party_name in partyname):
            pass
        else:
            partyname.append(rec.party_name)
    return render(request,'./GreyModule/reportFilter.html',{'date':d,'parties':processing_parties,'sendingparty':partyname})


def generateReport(request):
    selected_states=['In Process','Ready to print']
    selected_parties=[]
    lot=request.POST.get("lot_no")
    if lot == "":
        lot=None
    else:
        lot=int(lot)

    s = request.POST.get("checkbox")
    if s!=None:
        selected_parties.append(s)
        selected_party_object=get_object_or_404(GreyOutprocessAgenciesMaster,agency_name=selected_parties[0])
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

        begin1=begin
        end1=end
        begin=begin.strftime("%d/%m/%Y")                ######date string format change
        end=end.strftime("%d/%m/%Y")

        flag=0
        if(lot==None and selected_parties!=[]):
            rec = Record.objects.filter(state__in=selected_states,agency_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
            h1=str(selected_parties[0])
            h2=str(begin) + " - "+str(end)
            flag=1
        elif(lot!=None and selected_parties==[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,sent_to_processing_date__in=selected_dates).order_by('state')
            h1=str(lot)
            h2=str(begin) + " - "+str(end)
            flag=2
        elif(lot!=None and selected_parties!=[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,agency_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
            h1=str(selected_parties[0]) +" and lot no " +str(lot)
            h2=str(begin) + " - "+str(end)
            flag=3
        else:
            rec= Record.objects.filter(state__in=selected_states,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
            h1=""
            h2=str(begin) + " - "+str(end)
            flag=4
        lot_list=[]
        for r in rec:
            if r.lot_no in lot_list:
                pass
            else:
                lot_list.append(r.lot_no)


        data_row=[]
        data_block=[]
        for l in lot_list:
            totalthan=0
            pendingthan=0
            rec_lists=[]
            if(flag==1):
                rec2 = Record.objects.filter(state__in=selected_states,lot_no=l,agency_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==2):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==3):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,agency_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==4):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,sent_to_processing_date__in=selected_dates).order_by('state')

            for r in rec2:
                totalthan=totalthan+r.than
                rate=r.rate
                if r.state=="In Process":
                    pendingthan=pendingthan+r.than
                else:
                    rec=[r.sent_to_processing_date,r.gate_pass,r.quality.quality_name,r.than,r.mtrs,r.recieve_processed_date,r.chalan_no,r.state ]
                    rec_lists.append(rec)

            data_row=[l,totalthan,pendingthan,rec_lists,rate]
            data_block.append(data_row)

        return render(request,'./GreyModule/ledgerreport.html',{'data':data_block,'h1':h1,'h2':h2,'lot_no':lot,'party':s,'begin':str(begin1),'end':str(end1)})
    else:
        flag=0
        if(lot==None and selected_parties!=[]):
            rec = Record.objects.filter(state__in=selected_states,agency_name=selected_party_object).order_by('lot_no','state')
            h1=str(selected_parties[0])
            flag=1
        elif(lot!=None and selected_parties==[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot).order_by('state')
            h1=str(lot)
            flag=2
        elif(lot!=None and selected_parties!=[]):
            h1=str(selected_parties[0]) +" and lot no " +str(lot)
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,agency_name=selected_party_object).order_by('lot_no','state')
            flag=3
        else:
            messages.error(request,'Please enter valid input')
            return redirect('/reportFilter')
        lot_list=[]
        for r in rec:
            if r.lot_no in lot_list:
                pass
            else:
                lot_list.append(r.lot_no)
        print(lot_list)

        data_row=[]
        data_block=[]

        for l in lot_list:
            totalthan=0
            pendingthan=0
            if(flag==1):
                rec2 = Record.objects.filter(state__in=selected_states,lot_no=l,agency_name=selected_party_object).order_by('state')
            elif(flag==2):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l).order_by('state')
            else:
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,agency_name=selected_party_object).order_by('lot_no','state')

            rec_lists=[]
            for r in rec2:
                totalthan=totalthan+r.than
                rate=r.rate
                if r.state=="In Process":
                    pendingthan=pendingthan+r.than
                else:
                    rec=[r.sent_to_processing_date,r.gate_pass,r.quality.quality_name,r.than,r.mtrs,r.recieve_processed_date,r.chalan_no,r.state ]
                    rec_lists.append(rec)

            data_row=[l,totalthan,pendingthan,rec_lists,rate]
            data_block.append(data_row)
        return render(request,'./GreyModule/ledgerreport.html',{'data':data_block,'h1':h1,'h2':"",'lot_no':lot,'party':s})

############# PRINT LEDGER REPORT ###########
def printLedgerExcel(request):
    selected_states=['In Process','Ready to print']
    selected_parties=[]
    lot=request.POST.get("lot_no")
    if lot == "None":
        lot=None
    else:
        lot=int(lot)

    s = request.POST.get("agency_name")
    if s!="None":
        selected_parties.append(s)
        selected_party_object=get_object_or_404(GreyOutprocessAgenciesMaster,agency_name=selected_parties[0])
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

        begin1=begin
        end1=end
        begin=begin.strftime("%d/%m/%Y")                ######date string format change
        end=end.strftime("%d/%m/%Y")

        flag=0
        if(lot==None and selected_parties!=[]):
            rec = Record.objects.filter(state__in=selected_states,agency_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
            h1=str(selected_parties[0])
            h2=str(begin) + " - "+str(end)
            flag=1
        elif(lot!=None and selected_parties==[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,sent_to_processing_date__in=selected_dates).order_by('state')
            h1=str(lot)
            h2=str(begin) + " - "+str(end)
            flag=2
        elif(lot!=None and selected_parties!=[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,agency_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
            h1=str(selected_parties[0]) +" and lot no " +str(lot)
            h2=str(begin) + " - "+str(end)
            flag=3
        else:
            rec= Record.objects.filter(state__in=selected_states,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
            h1=""
            h2=str(begin) + " - "+str(end)
            flag=4
        lot_list=[]
        for r in rec:
            if r.lot_no in lot_list:
                pass
            else:
                lot_list.append(r.lot_no)


        data_row=[]
        data_block=[]
        for l in lot_list:
            totalthan=0
            pendingthan=0
            rec_lists=[]
            if(flag==1):
                rec2 = Record.objects.filter(state__in=selected_states,lot_no=l,agency_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==2):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==3):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,agency_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==4):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,sent_to_processing_date__in=selected_dates).order_by('state')

            for r in rec2:
                totalthan=totalthan+r.than
                rate=r.rate
                if r.state=="In Process":
                    pendingthan=pendingthan+r.than
                else:
                    rec=[r.sent_to_processing_date,r.gate_pass,r.quality.quality_name,r.than,r.mtrs,r.recieve_processed_date,r.chalan_no ]
                    rec_lists.append(rec)
            if len(rec_lists)!=0:
                flag=0
                for a in rec_lists:
                    if flag==0:
                        a.insert(0,l)
                        a.insert(1,totalthan)
                        a.insert(2,pendingthan)
                        a.insert(3,rate)
                        data_block.append(a)
                        flag=1
                    else:
                        a.insert(0,"")
                        a.insert(1,"")
                        a.insert(2,"")
                        a.insert(3,"")
                        data_block.append(a)
            else:
                data_row=[l,totalthan,pendingthan,rate]
                data_block.append(data_row)
            data_block.append(['','','','','','','','','','',''])

        columns=['Lot No','Total Than','Than Pending','Rate','sent date','Gate pass','Quality','Than','mtrs','recieve date','Chalan No']

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename=Ledger.xls'   #"Intransit-all.xls"

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Data')

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True


        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style) # at 0 row 0 column

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        #prev url req string to dict to querydict



        # rows = Record.objects.filter(state="godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
        for row in data_block:
            row_num += 1
            for col_num in range(len(row)):

                ws.write(row_num, col_num, str(row[col_num]), font_style)

        wb.save(response)

        return response


    else:
        flag=0
        if(lot==None and selected_parties!=[]):
            rec = Record.objects.filter(state__in=selected_states,agency_name=selected_party_object).order_by('lot_no','state')
            h1=str(selected_parties[0])
            flag=1
        elif(lot!=None and selected_parties==[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot).order_by('state')
            h1=str(lot)
            flag=2
        elif(lot!=None and selected_parties!=[]):
            h1=str(selected_parties[0]) +" and lot no " +str(lot)
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,agency_name=selected_party_object).order_by('lot_no','state')
            flag=3
        else:
            messages.error(request,'Please enter valid input')
            return redirect('/reportFilter')
        lot_list=[]
        for r in rec:
            if r.lot_no in lot_list:
                pass
            else:
                lot_list.append(r.lot_no)
        print(lot_list)

        data_row=[]
        data_block=[]

        for l in lot_list:
            totalthan=0
            pendingthan=0
            if(flag==1):
                rec2 = Record.objects.filter(state__in=selected_states,lot_no=l,agency_name=selected_party_object).order_by('state')
            elif(flag==2):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l).order_by('state')
            else:
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,agency_name=selected_party_object).order_by('lot_no','state')

            rec_lists=[]
            for r in rec2:
                totalthan=totalthan+r.than
                rate=r.rate
                if r.state=="In Process":
                    pendingthan=pendingthan+r.than
                else:
                    rec=[r.sent_to_processing_date,r.gate_pass,r.quality.quality_name,r.than,r.mtrs,r.recieve_processed_date,r.chalan_no ]
                    rec_lists.append(rec)

            if len(rec_lists)!=0:
                flag=0
                for a in rec_lists:
                    if flag==0:
                        a.insert(0,l)
                        a.insert(1,totalthan)
                        a.insert(2,pendingthan)
                        a.insert(3,rate)
                        data_block.append(a)
                        flag=1
                    else:
                        a.insert(0,"")
                        a.insert(1,"")
                        a.insert(2,"")
                        a.insert(3,"")
                        data_block.append(a)
            else:
                data_row=[l,totalthan,pendingthan,rate]
                data_block.append(data_row)
            data_block.append(['','','','','','','','','','',''])

        columns=['Lot No','Total Than','Than Pending','Rate','sent date','Gate pass','Quality','Than','mtrs','recieve date','Chalan No']

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename=Ledger.xls'   #"Intransit-all.xls"

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Data') # this will make a sheet named Users Data

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
        for row in data_block:
            row_num += 1
            for col_num in range(len(row)):

                ws.write(row_num, col_num, str(row[col_num]), font_style)

        wb.save(response)

        return response

############## GREY - DEFECTIVE STOCK ###############
def showDefective(request):
    records_list=Record.objects.filter(state__in=['Defect- Transport defect','Defect- Manufacturing defect'])
    records_filter = RecordFilter(request.GET,queryset=records_list)
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    quality_name=GreyQualityMaster.objects.all().order_by('quality_name')
    return render(request,'./GreyModule/defective.html',{'records':records,'filter':records_filter,'quality_name':quality_name})


################## GREY -  REPORT BY CHECKER BASED ##############
def checkerreportFilter(request):
    d=str(datetime.date.today().strftime('%Y-%m-%d'))
    checkers=Employee.objects.all().order_by('name')
    return render(request,'./GreyModule/checkerFilter.html',{'d':d,'checkers':checkers})

def checkerReport(request):
    c_id=int(request.POST.get('checker'))
    checker=get_object_or_404(Employee,id=c_id)
    begin = request.POST.get("start_date")
    end = request.POST.get("end_date")
    if(begin!="" or end!=""):

        begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
        end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
        selected_dates=[]

    # selected_quality=[]
        next_day = begin
        while True:
            if next_day > end:
                break
            selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
            next_day += datetime.timedelta(days=1)

        # quality_name = Quality.objects.all()
        datalist=[]

        total=[]
        totalthans=0
        totaltotal=0
        recs=Record.objects.filter(checker=checker,checking_date__in=selected_dates).order_by('lot_no','quality','checking_date')
        for r in recs:
            totalthans=totalthans+r.than

            l=[]
            l.append(r.quality.quality_name)
            l.append(r.checking_date)
            l.append(r.than)
            l.append(r.mtrs)
            mt=round((r.mtrs/r.than),2)
            l.append(mt)
            try:
                range=GreyCheckingCutRatesMaster.objects.filter(range1__lt=mt,range2__gt=mt).first()
                l.append(range.rate)

                l.append(round((mt*range.rate),2))
                totaltotal=totaltotal+round((mt*range.rate),2)
            except:
                l.append("rate not defined")
                l.append("rate not defined")
            l.append(r.lot_no)

            datalist.append(l)
        total.append(round(totalthans,2))
        total.append(round(totaltotal,2))

        begin = str(begin)
        end= str(end)
        display_begin=datetime.datetime.strptime(str(begin),"%Y-%m-%d").date().strftime("%d/%m/%Y")
        display_end=datetime.datetime.strptime(str(end),"%Y-%m-%d").date().strftime("%d/%m/%Y")
        return render(request,'./GreyModule/checkerReport.html',{'records':datalist,'total':total,'c':checker.name,'checker':checker.id,'begin':begin,'end':end,'display_begin':display_begin,'display_end':display_end})


################### Transport Report ######################

def transportreportFilter(request):
    d=str(datetime.date.today().strftime('%Y-%m-%d'))
    transport_agency=GreyTransportAgenciesMaster.objects.all().order_by('transport_agency_name')
    return render(request,'./GreyModule/transportFilter.html',{'d':d,'checkers':transport_agency})


def transportReport(request):
    t_id=int(request.POST.get('transport_agency_id'))
    transport_agency=get_object_or_404(GreyTransportAgenciesMaster,id=t_id)
    begin = request.POST.get("start_date")
    end = request.POST.get("end_date")
    if(begin!="" or end!=""):

        begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
        end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
        selected_dates=[]

    # selected_quality=[]
        next_day = begin
        while True:
            if next_day > end:
                break
            selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
            next_day += datetime.timedelta(days=1)

        datalist=[]

        total=[]
        totalbales=0
        totaltotal=0

        recs=Record.objects.filter(transport_agency=transport_agency,checking_date__in=selected_dates).order_by('lot_no','checking_date')
        lot_list=[]
        for r in recs:
            if r.lot_no not in lot_list:
                lot_list.append(r.lot_no)

        for l in lot_list:
            rec_one = Record.objects.filter(lot_no=l,transport_agency=transport_agency,checking_date__in=selected_dates).first()
            than_inlot = rec_one.total_thans
            bale_inlot = rec_one.total_bale
            records=get_list_or_404(Record,lot_no=l,transport_agency=transport_agency,checking_date__in=selected_dates)
            than_recieved=0
            for r in records:
                than_recieved=than_recieved+r.than
            if than_inlot==than_recieved:
                row_list=[l,rec_one.lr_no,rec_one.party_name,rec_one.quality.quality_name,bale_inlot,rec_one.transport_agency.rate,round(rec_one.transport_agency.rate*bale_inlot,2)]
                totalbales=totalbales+bale_inlot
                totaltotal=round(totaltotal + rec_one.transport_agency.rate*bale_inlot,2)
                datalist.append(row_list)


        total.append(round(totalbales,2))
        total.append(round(totaltotal,2))

        begin = str(begin)
        end= str(end)
        display_begin=datetime.datetime.strptime(str(begin),"%Y-%m-%d").date().strftime("%d/%m/%Y")
        display_end=datetime.datetime.strptime(str(end),"%Y-%m-%d").date().strftime("%d/%m/%Y")
        return render(request,'./GreyModule/transportReport.html',{'records':datalist,'total':total,'t':transport_agency.transport_agency_name,'checker':transport_agency.id,'begin':begin,'end':end,'display_begin':display_begin,'display_end':display_end})



################### QUALITY WISE REPORT ########################
def qualityreportFilter(request):
    quality_name= GreyQualityMaster.objects.all().order_by('quality_name')
    return render(request,'./GreyModule/qualityreportFilter.html',{'quality_name':quality_name})

def qualityReport(request):
    # quality_name=[]
    final_qs=[]
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
    quality_name= GreyQualityMaster.objects.all()
    selected_quality=[]
    for q in quality_name:

        if(request.POST.get(q.quality_name)!=None):
            selected_quality.append(request.POST.get(q.quality_name))
            rec_transit=Record.objects.filter(state="Transit",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.quality_name))))
            tally_than=0
            tally_mtrs=0
            total_than_in_transit=0
            total_mtrs_in_transit=0

            for r in rec_transit:
                total_than_in_transit=total_than_in_transit+r.than
                total_mtrs_in_transit=total_mtrs_in_transit+r.mtrs
            trthan=trthan+total_than_in_transit
            trmtrs=trmtrs+total_mtrs_in_transit

            rec_godown=Record.objects.filter(state="Godown",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.quality_name))))
            total_than_in_godown=0
            total_mtrs_in_godown=0
            for r in rec_godown:
                total_than_in_godown=total_than_in_godown+r.than
                total_mtrs_in_godown=total_mtrs_in_godown+r.mtrs
            gothan=gothan+total_than_in_godown
            gomtrs=gomtrs+total_mtrs_in_godown

            rec_checked=Record.objects.filter(state="Checked",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.quality_name))))
            total_than_in_checked=0
            total_mtrs_in_checked=0
            for r in rec_checked:
                total_than_in_checked=total_than_in_checked+r.than
                total_mtrs_in_checked=total_mtrs_in_checked+r.mtrs
            chthan=chthan+total_than_in_checked
            chmtrs=chmtrs+total_mtrs_in_checked

            rec_process=Record.objects.filter(state="In Process",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.quality_name))))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            rec_ready=Record.objects.filter(state="Ready to print",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.quality_name))))
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

            d1=[q.quality_name,
            total_than_in_transit,round(total_mtrs_in_transit,2),
            total_than_in_godown,round(total_mtrs_in_godown,2),
            total_than_in_checked,round(total_mtrs_in_checked,2),
            total_than_in_process,round(total_mtrs_in_process,2),
            total_than_in_ready,round(total_mtrs_in_ready,2),
            tally_than,round(tally_mtrs,2)
            ]

            final_qs.append(d1)
    total_all=[round(trthan,2),round(trmtrs,2),
            round(gothan,2),round(gomtrs,2),
            round(chthan,2),round(chmtrs,2),
            round(prthan,2),round(prmtrs,2),
            round(rethan,2),round(remtrs,2),
            round(tothan,2),round(tomtrs,2),
    ]
            # d=[d1,[1,2,3,4,5],[1,2,3,4,5],[1,2,3,4,5]]
    return render(request,'./GreyModule/qualityreport.html',{'data':final_qs,'total':total_all,'select':selected_quality})
################### QUALITY WISE REPORT END########################

################### QUALITY WISE LEDGER ########################
def qualityReport2filter(request):
    party=GreyOutprocessAgenciesMaster.objects.all().order_by('agency_name')
    quality_name=GreyQualityMaster.objects.all().order_by('quality_name')
    return render(request,'./GreyModule/qualityreport2filter.html',{'quality_name':quality_name,'parties':party})


def qualityReport2(request):
    begin = request.POST.get("start_date")
    end = request.POST.get("end_date")
    if(begin!="" or end!=""):

        begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
        end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
        selected_dates=[]

    # selected_quality=[]
        next_day = begin
        while True:
            if next_day > end:
                break
            selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
            next_day += datetime.timedelta(days=1)
        print(selected_dates)
    party_id=int(request.POST.get('checkbox'))
    outprocess_agency=get_object_or_404(GreyOutprocessAgenciesMaster,id=party_id)
    final_qs=[]
    total_all=[]

    prthan=0
    prmtrs=0
    rethan=0
    remtrs=0
    tothan=0
    tomtrs=0

    quality_name= GreyQualityMaster.objects.all().order_by('quality_name')
    selected_quality=[]
    for q in quality_name:

        if(request.POST.get(q.quality_name)!=None):
            selected_quality.append(request.POST.get(q.quality_name))

            if(begin!="" or end!=""):
                rec_process=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="In Process",agency = outprocess_agency,quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.quality_name))))
            else:
                rec_process=Record.objects.filter(state="In Process",agency=outprocess_agency,quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.quality_name))))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            if(begin!="" or end!=""):
                rec_ready=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="Ready to print",agency = outprocess_agency,quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.quality_name))))
            else:
                rec_ready=Record.objects.filter(state="Ready to print",agency = outprocess_agency,quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.quality_name))))

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

            d1=[q.quality_name,
            total_than_in_process,round(total_mtrs_in_process,2),
            total_than_in_ready,round(total_mtrs_in_ready,2),
            tally_than,round(tally_mtrs,2),
            round(tally_than-total_than_in_ready,2),round(tally_mtrs-total_mtrs_in_ready,2)
            ]
            if(d1[1]==0 and d1[2]==0 and d1[3]==0 and d1[4]==0):
                pass
            else:
                final_qs.append(d1)
    total_all=[round(prthan,2),round(prmtrs,2),
            round(rethan,2),round(remtrs,2),
            round(tothan,2),round(tomtrs,2),
            round(tothan-rethan,2),round(tomtrs-remtrs,2)
    ]
    if selected_quality==[]:
        messages.error(request,"Please select atleast one grey quality")
        return redirect('/qualitypartyreportFilter')
    if(begin!="" or end!=""):
        return render(request,'./GreyModule/qualitypartyreport.html',{'data':final_qs,'total':total_all,'select':selected_quality,'party':outprocess_agency.agency_name,'begin':str(begin),'end':str(end)})
    else:
        return render(request,'./GreyModule/qualitypartyreport.html',{'data':final_qs,'total':total_all,'select':selected_quality,'party':outprocess_agency.agency_name})
################### QUALITY WISE LEDGER END########################




############## LOTS #############
def lotList(request):
    lotsList = GreyLots.objects.all().order_by('grey_lot_number')
    quality = GreyQualityMaster.objects.all()
    paginator = Paginator(lotsList,10)
    page = request.GET.get('page')
    lots = paginator.get_page(page)
    return render(request,'./GreyModule/greyLots.html',{'lots':lots, 'quality':quality})

def assignLot(request):
    bill_number=request.POST.get("bill_number")
    bill_date=request.POST.get("bill_date")
    bill_amount=request.POST.get("bill_amount")
    bale=request.POST.get("bale")
    meters=request.POST.get("meters")
    lr_number=request.POST.get("lr_number")
    order_number = request.POST.get("order_number")
    transport_agency = request.POST.get("transport_agency")
    if  bill_date=="" or  bill_number=="" or bill_amount=="" or lr_number=="" or order_number=="":
        messages.error(request,"Please fill all the fields")
        return redirect('/ordersList')
    transport_agency = GreyTransportAgenciesMaster.objects.get(transport_agency_name=transport_agency)
    order = GreyOrders.objects.get(order_number=order_number)
    # order_status_obj= OrderStatus.objects.get(status_id=order.order_status.status_id)
    order_status_obj = OrderStatus()
    order_status_obj.order_status= "Assigned Lot"
    # print(order_status_obj.order_status)
    order_status_obj.save()
    order.order_status = order_status_obj
    # print(order.order_status.order_status)
    order.save()
    rate = float(float(meters)/float(order.thans))
    new_status = LotStatus(type="Initial State")
    new_status.save()
    new_lot = GreyLots(
        bill_number = bill_number,
        bill_date = bill_date,
        bill_amount = bill_amount,
        lr_number = lr_number,
        bale = bale,
        rate = rate,
        order_number = order,
        lot_status=new_status,
        meters = meters,
        transport_agency = transport_agency
        )
    print(rate)
    new_lot.save()
    messages.success(request,"Lot Assigned")
    return redirect('/lotList')

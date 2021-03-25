from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,GreyQualitiesMaster,GreyCheckingCutRatesMaster,GreyOutprocessAgenciesMaster,GreyGodownsMaster, GreyTransportAgenciesMaster, GreySuppliersMaster
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
    return render(request, './GreyModule/greyhome.html')

def greyorders(request):
    return render(request, './GreyModule/greyorders.html')

def greylots(request):
    return render(request, './GreyModule/greylots.html')

def greyPlaceOrder(request):
    return render(request, './GreyModule/greyPlaceOrder.html')

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
                q_object=get_object_or_404(GreyQualitiesMaster,
                    qualities=data[6])
            except:
                q_object = GreyQualitiesMaster(
                    qualities=data[6]
                    )
                q_object.save()
            quality_object=get_object_or_404(GreyQualitiesMaster,qualities=data[6])
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
                # print(datetime.datetime.strptime(d[0:10], '%Y-%m-%d').strftime('%b %d,%Y'))
                counter = counter + 1
                # try:
                #     rec=get_object_or_404(Quality,
                #         qualities=data[6])
                # except:
                #     new_quality = Quality(
                #         qualities=data[6]
                #         )
                #     new_quality.save()

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
    qualities=GreyQualitiesMaster.objects.all().order_by('qualities')

    return render(request, './GreyModule/intransit.html',{'records':records,'filter':records_filter,'sums':sums,'qualities':qualities})

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
    qualities=GreyQualitiesMaster.objects.all().order_by('qualities')
    return render(request, './GreyModule/godown.html',{'records':records,'filter':records_filter,'sums':sums,'qualities':qualities})

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
    qualities=GreyQualitiesMaster.objects.all().order_by('qualities')
    return render(request, './GreyModule/record.html', {'record':rec,'qualities':qualities})

###### GODOWN APPROVE FORM ######
def goDownApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    mindate=datetime.datetime.strptime(rec.bill_date,'%b %d,%Y').strftime('%Y-%m-%d')
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    qualities = GreyQualitiesMaster.objects.all()
    d=datetime.date.today()
    d=str(d)
    return render(request, './GreyModule/godownapprove.html', {'record':rec,'qualities':qualities,'mindate':mindate,'maxdate':maxdate,'date':d})

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
        quality_ob=get_object_or_404(GreyQualitiesMaster,id=int(q_id))
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
    qualities=GreyQualitiesMaster.objects.all().order_by('qualities')
    return render(request, './GreyModule/checking.html',{'records':records,'filter':records_filter,'sums':sums,'qualities':qualities})

def showCheckingRequest(request):
    records_list=Record.objects.filter(state="Godown").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, './GreyModule/checkingrequest.html',{'records':records,'filter':records_filter})

def checkingApprove(request,id):
    rec=get_object_or_404(Record, id=id)

    mindate=str(rec.recieving_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    qualities_all = GreyQualitiesMaster.objects.all().order_by('qualities')
    checkers=Employee.objects.all().order_by('name')
    transports=GreyTransportAgenciesMaster.objects.all().order_by('transport')
    d=datetime.date.today()
    d=str(d)
    return render(request, './GreyModule/checkingapprove.html', {'date':d,'record':rec,'transport':transports,'checkers':checkers,'qualities':qualities_all,'mindate':mindate,'maxdate':maxdate})

def approveCheck(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_recieved")
    than_recieved = int(than_recieved)
    defect=request.POST.get("defect")
    mtrs_edit=request.POST.get("mtrs-checked")

    checker_id=int(request.POST.get("checker"))
    checker=get_object_or_404(Employee,id=checker_id)
    t=int(request.POST.get("transport"))
    transport=get_object_or_404(GreyTransportAgenciesMaster,id=t)

    q_id=int(request.POST.get("new-quality"))
    quality_object=get_object_or_404(GreyQualitiesMaster,id=q_id)

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
            prevRec.transport=transport

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
                transport=transport

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
            prevRec.transport=transport
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
                transport=transport

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
    qualities=GreyQualitiesMaster.objects.all().order_by('qualities')
    return render(request, './GreyModule/processing.html',{'records':records,'filter':records_filter,'sums':sums,'qualities':qualities})

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
    processing_parties = GreyOutprocessAgenciesMaster.objects.all().order_by('processing_party')
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
        prevRec.processing_party_name=partyprocessing
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
            processing_party_name = partyprocessing,
            processing_type = process_type,
            checking_date = prevRec.checking_date,
            sent_to_processing_date=str(request.POST["sending_date"]),
            total_thans=prevRec.total_thans,
            total_mtrs=prevRec.total_mtrs,
            gate_pass = int(request.POST.get('gatepass')),
            checker=prevRec.checker,
            transport=prevRec.transport

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
    qualities=GreyQualitiesMaster.objects.all().order_by('qualities')
    return render(request, './GreyModule/readytoprint.html',{'records':records,'filter':records_filter,'sums':sums,'qualities':qualities})

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
            processing_party_name = prevRec.processing_party_name,
            sent_to_processing_date = prevRec.sent_to_processing_date,
            recieve_processed_date=str(request.POST.get("processing_date")),
            total_mtrs=prevRec.total_mtrs,
            total_thans=prevRec.total_thans,
            godown_name=location,
            processing_type=prevRec.processing_type,
            gate_pass=prevRec.gate_pass,
            chalan_no = int(request.POST.get('chalan')),
            checker=prevRec.checker,
            transport=prevRec.transport,
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
    processing_parties = GreyOutprocessAgenciesMaster.objects.all().order_by('processing_party')
    partyname =[]
    records = Record.objects.all().order_by('party_name')
    d=str(datetime.date.today())
    for rec in records:
        if(rec.party_name in partyname):
            pass
        else:
            partyname.append(rec.party_name)
    return render(request,'./GreyModule/reportfilter.html',{'date':d,'parties':processing_parties,'sendingparty':partyname})


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
        selected_party_object=get_object_or_404(GreyOutprocessAgenciesMaster,processing_party=selected_parties[0])
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
            rec = Record.objects.filter(state__in=selected_states,processing_party_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
            h1=str(selected_parties[0])
            h2=str(begin) + " - "+str(end)
            flag=1
        elif(lot!=None and selected_parties==[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,sent_to_processing_date__in=selected_dates).order_by('state')
            h1=str(lot)
            h2=str(begin) + " - "+str(end)
            flag=2
        elif(lot!=None and selected_parties!=[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,processing_party_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
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
                rec2 = Record.objects.filter(state__in=selected_states,lot_no=l,processing_party_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==2):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==3):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,processing_party_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==4):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,sent_to_processing_date__in=selected_dates).order_by('state')

            for r in rec2:
                totalthan=totalthan+r.than
                rate=r.rate
                if r.state=="In Process":
                    pendingthan=pendingthan+r.than
                else:
                    rec=[r.sent_to_processing_date,r.gate_pass,r.quality.qualities,r.than,r.mtrs,r.recieve_processed_date,r.chalan_no,r.state ]
                    rec_lists.append(rec)

            data_row=[l,totalthan,pendingthan,rec_lists,rate]
            data_block.append(data_row)

        return render(request,'./GreyModule/ledgerreport.html',{'data':data_block,'h1':h1,'h2':h2,'lot_no':lot,'party':s,'begin':str(begin1),'end':str(end1)})
    else:
        flag=0
        if(lot==None and selected_parties!=[]):
            rec = Record.objects.filter(state__in=selected_states,processing_party_name=selected_party_object).order_by('lot_no','state')
            h1=str(selected_parties[0])
            flag=1
        elif(lot!=None and selected_parties==[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot).order_by('state')
            h1=str(lot)
            flag=2
        elif(lot!=None and selected_parties!=[]):
            h1=str(selected_parties[0]) +" and lot no " +str(lot)
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,processing_party_name=selected_party_object).order_by('lot_no','state')
            flag=3
        else:
            messages.error(request,'Please enter valid input')
            return redirect('/reportfilter')
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
                rec2 = Record.objects.filter(state__in=selected_states,lot_no=l,processing_party_name=selected_party_object).order_by('state')
            elif(flag==2):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l).order_by('state')
            else:
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,processing_party_name=selected_party_object).order_by('lot_no','state')

            rec_lists=[]
            for r in rec2:
                totalthan=totalthan+r.than
                rate=r.rate
                if r.state=="In Process":
                    pendingthan=pendingthan+r.than
                else:
                    rec=[r.sent_to_processing_date,r.gate_pass,r.quality.qualities,r.than,r.mtrs,r.recieve_processed_date,r.chalan_no,r.state ]
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

    s = request.POST.get("processing_party")
    if s!="None":
        selected_parties.append(s)
        selected_party_object=get_object_or_404(GreyOutprocessAgenciesMaster,processing_party=selected_parties[0])
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
            rec = Record.objects.filter(state__in=selected_states,processing_party_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
            h1=str(selected_parties[0])
            h2=str(begin) + " - "+str(end)
            flag=1
        elif(lot!=None and selected_parties==[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,sent_to_processing_date__in=selected_dates).order_by('state')
            h1=str(lot)
            h2=str(begin) + " - "+str(end)
            flag=2
        elif(lot!=None and selected_parties!=[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,processing_party_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('lot_no','state')
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
                rec2 = Record.objects.filter(state__in=selected_states,lot_no=l,processing_party_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==2):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==3):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,processing_party_name=selected_party_object,sent_to_processing_date__in=selected_dates).order_by('state')

            elif(flag==4):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,sent_to_processing_date__in=selected_dates).order_by('state')

            for r in rec2:
                totalthan=totalthan+r.than
                rate=r.rate
                if r.state=="In Process":
                    pendingthan=pendingthan+r.than
                else:
                    rec=[r.sent_to_processing_date,r.gate_pass,r.quality.qualities,r.than,r.mtrs,r.recieve_processed_date,r.chalan_no ]
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
            rec = Record.objects.filter(state__in=selected_states,processing_party_name=selected_party_object).order_by('lot_no','state')
            h1=str(selected_parties[0])
            flag=1
        elif(lot!=None and selected_parties==[]):
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot).order_by('state')
            h1=str(lot)
            flag=2
        elif(lot!=None and selected_parties!=[]):
            h1=str(selected_parties[0]) +" and lot no " +str(lot)
            rec= Record.objects.filter(state__in=selected_states,lot_no=lot,processing_party_name=selected_party_object).order_by('lot_no','state')
            flag=3
        else:
            messages.error(request,'Please enter valid input')
            return redirect('/reportfilter')
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
                rec2 = Record.objects.filter(state__in=selected_states,lot_no=l,processing_party_name=selected_party_object).order_by('state')
            elif(flag==2):
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l).order_by('state')
            else:
                rec2= Record.objects.filter(state__in=selected_states,lot_no=l,processing_party_name=selected_party_object).order_by('lot_no','state')

            rec_lists=[]
            for r in rec2:
                totalthan=totalthan+r.than
                rate=r.rate
                if r.state=="In Process":
                    pendingthan=pendingthan+r.than
                else:
                    rec=[r.sent_to_processing_date,r.gate_pass,r.quality.qualities,r.than,r.mtrs,r.recieve_processed_date,r.chalan_no ]
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
    qualities=GreyQualitiesMaster.objects.all().order_by('qualities')
    return render(request,'./GreyModule/defective.html',{'records':records,'filter':records_filter,'qualities':qualities})


################## GREY -  REPORT BY CHECKER BASED ##############
def checkerReportFilter(request):
    d=str(datetime.date.today().strftime('%Y-%m-%d'))
    checkers=Employee.objects.all().order_by('name')
    return render(request,'./GreyModule/checkerfilter.html',{'d':d,'checkers':checkers})

def checkerReport(request):
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

        total=[]
        totalthans=0
        totaltotal=0
        recs=Record.objects.filter(checker=checker,checking_date__in=selected_dates).order_by('lot_no','quality','checking_date')
        for r in recs:
            totalthans=totalthans+r.than

            l=[]
            l.append(r.quality.qualities)
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
        return render(request,'./GreyModule/checkerreport.html',{'records':datalist,'total':total,'c':checker.name,'checker':checker.id,'begin':begin,'end':end,'display_begin':display_begin,'display_end':display_end})


################### Transport Report ######################

def transportReportFilter(request):
    d=str(datetime.date.today().strftime('%Y-%m-%d'))
    transport=GreyTransportAgenciesMaster.objects.all().order_by('transport')
    return render(request,'./GreyModule/transportfilter.html',{'d':d,'checkers':transport})


def transportReport(request):
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

        total=[]
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


        total.append(round(totalbales,2))
        total.append(round(totaltotal,2))

        begin = str(begin)
        end= str(end)
        display_begin=datetime.datetime.strptime(str(begin),"%Y-%m-%d").date().strftime("%d/%m/%Y")
        display_end=datetime.datetime.strptime(str(end),"%Y-%m-%d").date().strftime("%d/%m/%Y")
        return render(request,'./GreyModule/transportreport.html',{'records':datalist,'total':total,'t':transport.transport,'checker':transport.id,'begin':begin,'end':end,'display_begin':display_begin,'display_end':display_end})



################### QUALITY WISE REPORT ########################
def qualityReportFilter(request):
    qualities= GreyQualitiesMaster.objects.all().order_by('qualities')
    return render(request,'./GreyModule/qualityreportfilter.html',{'qualities':qualities})

def qualityReport(request):
    # qualities=[]
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
    qualities= GreyQualitiesMaster.objects.all()
    selected_qualities=[]
    for q in qualities:

        if(request.POST.get(q.qualities)!=None):
            selected_qualities.append(request.POST.get(q.qualities))
            rec_transit=Record.objects.filter(state="Transit",quality=get_object_or_404(GreyQualitiesMaster,id=int(request.POST.get(q.qualities))))
            tally_than=0
            tally_mtrs=0
            total_than_in_transit=0
            total_mtrs_in_transit=0

            for r in rec_transit:
                total_than_in_transit=total_than_in_transit+r.than
                total_mtrs_in_transit=total_mtrs_in_transit+r.mtrs
            trthan=trthan+total_than_in_transit
            trmtrs=trmtrs+total_mtrs_in_transit

            rec_godown=Record.objects.filter(state="Godown",quality=get_object_or_404(GreyQualitiesMaster,id=int(request.POST.get(q.qualities))))
            total_than_in_godown=0
            total_mtrs_in_godown=0
            for r in rec_godown:
                total_than_in_godown=total_than_in_godown+r.than
                total_mtrs_in_godown=total_mtrs_in_godown+r.mtrs
            gothan=gothan+total_than_in_godown
            gomtrs=gomtrs+total_mtrs_in_godown

            rec_checked=Record.objects.filter(state="Checked",quality=get_object_or_404(GreyQualitiesMaster,id=int(request.POST.get(q.qualities))))
            total_than_in_checked=0
            total_mtrs_in_checked=0
            for r in rec_checked:
                total_than_in_checked=total_than_in_checked+r.than
                total_mtrs_in_checked=total_mtrs_in_checked+r.mtrs
            chthan=chthan+total_than_in_checked
            chmtrs=chmtrs+total_mtrs_in_checked

            rec_process=Record.objects.filter(state="In Process",quality=get_object_or_404(GreyQualitiesMaster,id=int(request.POST.get(q.qualities))))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            rec_ready=Record.objects.filter(state="Ready to print",quality=get_object_or_404(GreyQualitiesMaster,id=int(request.POST.get(q.qualities))))
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

            d1=[q.qualities,
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
    return render(request,'./GreyModule/qualityreport.html',{'data':final_qs,'total':total_all,'select':selected_qualities})
################### QUALITY WISE REPORT END########################

################### QUALITY WISE LEDGER ########################
def qualityReport2filter(request):
    party=GreyOutprocessAgenciesMaster.objects.all().order_by('processing_party')
    qualities=GreyQualitiesMaster.objects.all().order_by('qualities')
    return render(request,'./GreyModule/qualityreport2filter.html',{'qualities':qualities,'parties':party})


def qualityReport2(request):
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
        print(selected_dates)
    party_id=int(request.POST.get('checkbox'))
    party_ob=get_object_or_404(GreyOutprocessAgenciesMaster,id=party_id)
    final_qs=[]
    total_all=[]

    prthan=0
    prmtrs=0
    rethan=0
    remtrs=0
    tothan=0
    tomtrs=0

    qualities= GreyQualitiesMaster.objects.all().order_by('qualities')
    selected_qualities=[]
    for q in qualities:

        if(request.POST.get(q.qualities)!=None):
            selected_qualities.append(request.POST.get(q.qualities))

            if(begin!="" or end!=""):
                rec_process=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="In Process",processing_party_name=party_ob,quality=get_object_or_404(GreyQualitiesMaster,id=int(request.POST.get(q.qualities))))
            else:
                rec_process=Record.objects.filter(state="In Process",processing_party_name=party_ob,quality=get_object_or_404(GreyQualitiesMaster,id=int(request.POST.get(q.qualities))))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            if(begin!="" or end!=""):
                rec_ready=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="Ready to print",processing_party_name=party_ob,quality=get_object_or_404(GreyQualitiesMaster,id=int(request.POST.get(q.qualities))))
            else:
                rec_ready=Record.objects.filter(state="Ready to print",processing_party_name=party_ob,quality=get_object_or_404(GreyQualitiesMaster,id=int(request.POST.get(q.qualities))))

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

            d1=[q.qualities,
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
    if selected_qualities==[]:
        messages.error(request,"Please select atleast one grey quality")
        return redirect('/qualitypartyreportfilter')
    if(begin!="" or end!=""):
        return render(request,'./GreyModule/qualitypartyreport.html',{'data':final_qs,'total':total_all,'select':selected_qualities,'party':party_ob.processing_party,'begin':str(begin),'end':str(end)})
    else:
        return render(request,'./GreyModule/qualitypartyreport.html',{'data':final_qs,'total':total_all,'select':selected_qualities,'party':party_ob.processing_party})
################### QUALITY WISE LEDGER END########################




######### GREY - CUT RANGE MASTER ########

def renderGreyMasterCheckingCutRates(request):
    all_cut_ranges = GreyCheckingCutRatesMaster.objects.all().order_by('cut_start_range')
    paginator = Paginator(all_cut_ranges,10)
    page = request.GET.get('page')
    cut_ranges = paginator.get_page(page)
    return render(request,'./GreyModule/masterGreyCheckingCutRates.html',{'records':cut_ranges})

def saveGreyMasterCheckingCutRate(request):
    start_range = float(request.POST.get("cut_start_range"))
    end_range = float(request.POST.get("cut_end_range"))
    existingrange = GreyCheckingCutRatesMaster.objects.all()
    flag = 0

    for i in existingrange:
        if i.cut_start_range<start_range<i.cut_end_range or i.cut_start_range<end_range<i.cut_end_range:
            flag = flag + 1
            break

    if flag == 0:

        newRecord = GreyCheckingCutRatesMaster(
            cut_start_range = start_range,
            cut_end_range = end_range,
            checking_rate = float(request.POST.get('rate'))
        )

        newRecord.save()
        messages.success(request,'Range added')
        return redirect('/renderGreyMasterCheckingCutRates')

    else:

        messages.error(request,'Range already exists')
        return redirect('/renderGreyMasterCheckingCutRates')

def deleteGreyMasterCheckingCutRate(request,id):
    GreyCheckingCutRatesMaster.objects.filter(id=id).delete()
    messages.success(request,"Range deleted")
    return redirect('/renderGreyMasterCheckingCutRates')


############ GREY : QUALITY MASTER ############

def renderGreyMasterQuality(request):
    all_qualities = GreyQualitiesMaster.objects.all().order_by('qualities')
    #return render(request,'./GreyModule/addquality.html',{'allqualities':all_qualities})
    paginator = Paginator(all_qualities,10)
    page = request.GET.get('page')
    qualities = paginator.get_page(page)

    return render(request,'./GreyModule/masterGreyQualities.html',{'records':qualities})

def saveGreyMasterQuality(request):
    quality_name = request.POST.get("quality_name")
    quality_name = quality_name.strip()

    quality_name = quality_name.replace('"','inch')
    try:
        existing_quality=get_object_or_404(GreyQualitiesMaster,qualities=quality_name.upper())
        messages.error(request,"This quality already exists")
    except:
        if quality_name.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/renderMasterQuality')
        new_quality = GreyQualitiesMaster(
            qualities=quality_name.upper()
        )
        new_quality.save()
        messages.success(request,"Grey Quality added")
    return redirect('/renderGreyMasterQuality')

def deleteGreyMasterQuality(request,id):
    try:
        GreyQualitiesMaster.objects.filter(id=id).delete()
        messages.success(request,"Grey Quality deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/renderGreyMasterQuality')

def renderEditGreyMasterQuality(request,id):
    quality=get_object_or_404(GreyQualitiesMaster,id=id)
    return render(request,'./GreyModule/editGreyMasterQuality.html',{'id':id,'name':quality.qualities})

def editGreyMasterQuality(request,id):
    quality=get_object_or_404(GreyQualitiesMaster,id=id)
    p=request.POST.get("edit-grey-quality")
    p = p.upper()
    p = p.strip()
    quality.qualities = p
    quality.save()
    messages.success(request,"Grey Quality edited")
    return redirect('/renderGreyMasterQuality')


###### GREY : Processing House Party Master #######

def renderGreyMasterOutprocessAgencies(request):
    parties_all = GreyOutprocessAgenciesMaster.objects.all().order_by('agency_name')

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./GreyModule/masterGreyOutprocessAgencies.html',{'records':parties})

def saveGreyMasterOutprocessAgency(request):
    p = request.POST.get("outprocess-agency")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(GreyOutprocessAgenciesMaster,agency_name=p)
        messages.error(request,"This Outprocess Agency already exists")
    except:
        if p.strip()=="":
            messages.error(request,"Please enter valid input")
            return redirect('/renderGreyMasterOutprocessAgencies')
        new_Party = GreyOutprocessAgenciesMaster(
            agency_name= p
        )
        new_Party.save()
        messages.success(request,"Outprocess Agency added successfully")
    return redirect('/renderGreyMasterOutprocessAgencies')

def deleteGreyMasterOutprocessAgency(request,id):
    try:
        GreyOutprocessAgenciesMaster.objects.filter(id=id).delete()
        messages.success(request,"Outprocess Agency Deleted")
    except:
        messages.error(request,"Cannot delete this Outprocess Agency since it is being used")
    return redirect('/renderGreyMasterOutprocessAgencies')

def renderEditGreyMasterOutprocessAgency(request,id):
    party=get_object_or_404(GreyOutprocessAgenciesMaster,id=id)
    return render(request,'./GreyModule/editOutprocessAgency.html',{'id':id,'name':party.agency_name})

def editGreyMasterOutprocessAgency(request,id):
    party=get_object_or_404(GreyOutprocessAgenciesMaster,id=id)
    p=request.POST.get("edit-outprocess-agency")
    p = p.upper()
    p = p.strip()
    party.agency_name = p
    party.save()
    messages.success(request,"Outprocess Agency edited")
    return redirect('/renderGreyMasterOutprocessAgencies')


########## Transport Agency Master ###########

def renderGreyMasterTransportAgencies(request):
    parties_all = GreyTransportAgenciesMaster.objects.all().order_by('transport_agency_name')
    #return render(request,'./GreyModule/addparty.html',{'parties':parties_all})

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./GreyModule/masterGreyTransportAgencies.html',{'records':parties})

def saveTransportAgency(request):
    p = request.POST.get("transport_agency_name")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(GreyTransportAgenciesMaster,transport=p)
        messages.error(request,"This Transport Agency already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/renderGreyMasterTransportAgencies')
        new_Party = GreyTransportAgenciesMaster(
            transport_agency_name= p,
            rate=float(request.POST.get('rate'))
        )
        new_Party.save()
        messages.success(request,"Transport Agency added successfully")
    return redirect('/renderGreyMasterTransportAgencies')

def deleteTransportAgency(request,id):
    try:
        GreyTransportAgenciesMaster.objects.filter(id=id).delete()
        messages.success(request,"Transport Agency deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/renderGreyMasterTransportAgencies')

def renderEditTransportAgency(request,id):
    party=get_object_or_404(GreyTransportAgenciesMaster,id=id)
    return render(request,'./GreyModule/edittransport.html',{'id':id,'name':party.transport_agency_name,'rate':party.rate})

def editTransportAgency(request,id):
    party=get_object_or_404(GreyTransportAgenciesMaster,id=id)
    p=request.POST.get("transport_agency_name")
    p = p.upper()
    p = p.strip()
    party.transport_agency_name = p
    party.rate = float(request.POST.get('rate'))
    party.save()
    messages.success(request,"Transport Agency edited")
    return redirect('/renderGreyMasterTransportAgencies')


####### GREY : Godown MASTER #######

def renderGreyMasterGodowns(request):
    all_grey_godowns = GreyGodownsMaster.objects.all().order_by('godown_name')
    paginator = Paginator(all_grey_godowns,10)
    page = request.GET.get('page')
    locations = paginator.get_page(page)
    return render(request,'./GreyModule/masterGreyGodowns.html',{'records':locations})

def saveGreyMasterGodown(request):
    p = request.POST.get("grey-godown-name")
    p = p.strip().upper()
    try:
        existing_party=get_object_or_404(GreyGodownsMaster,godown_name=p)
        messages.error(request,"This Grey Godown already exists")
    except:
        if p.strip()=="":
            messages.error(request,"Please enter valid input")
            return redirect('/renderGreyMasterGodowns')
        new_loc = GreyGodownsMaster(
            godown_name= p
        )
        new_loc.save()
        messages.success(request,"Grey Added in master list successfully")
    return redirect('/renderGreyMasterGodowns')

def deleteGreyMasterGodown(request,id):
    try:
        GreyGodownsMaster.objects.filter(id=id).delete()
        messages.success(request,"Grey Godown deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/renderGreyMasterGodowns')

def renderEditGreyMasterGodown(request,id):
    grey_godown = get_object_or_404(GreyGodownsMaster,id=id)
    return render(request,'./GreyModule/editGreyMasterGodown.html',{'id':id,'name':grey_godown.godown_name})

def editGreyMasterGodown(request,id):
    grey_godown = get_object_or_404(GreyGodownsMaster,id=id)
    godown_name = request.POST.get("edit-grey-godown")
    grey_godown.godown_name = godown_name.upper().strip()
    grey_godown.save()
    messages.success(request, "Grey godown edited")
    return redirect('/renderGreyMasterGodowns')




############## SUPPLIER MASTER #############


def greyMasterSupplier(request):
    all_checker = GreySuppliersMaster.objects.all().order_by('supplier_name')
    paginator = Paginator(all_checker,10)
    page = request.GET.get('page')
    checkers = paginator.get_page(page)

    return render(request,'./GreyModule/greyMasterSupplier.html',{'records':checkers})

def saveGreySupplier(request):
    q=request.POST.get("id")
    # q = q.strip()
    l=(request.POST.get("supplier_name"))

    m=request.POST.get("address")
    m = m.strip()
    n=request.POST.get("city")
    n = n.strip()
    o=request.POST.get("contact_number")
    o = o.strip()
    p=request.POST.get("email")
    p = p.strip()

    r=request.POST.get("remarks")
    r = r.strip()


    try:
        existing_quality=get_object_or_404(GreySuppliersMaster,id=q,supplier_name=l)
        messages.error(request,"This checker already exists")
    except:
        if  m=="" or n=="" or o=="" or p=="" or q=="" or l=="":
            messages.error(request,"please enter valid input")
            return redirect('/greyMasterSupplier')
        new_quality = GreySuppliersMaster(
            id = q,
            supplier_name = l,
            city = n.upper(),
            address = m.upper(),
            email=p,
            contact_number=o,
            remarks=r.upper()

        )
        new_quality.save()
        messages.success(request,"Supplier added")
    return redirect('/greyMasterSupplier')

def deleteGreySupplier(request,id):
    try:
        GreySuppliersMaster.objects.filter(id=id).delete()
        messages.success(request,"Supplier deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/greyMasterSupplier')

def renderEditGreySupplier(request,id):
    quality=get_object_or_404(GreySuppliersMaster,id=id)
    return render(request,'./GreyModule/editGreySupplier.html',{'id':id,'record':quality})

def editGreySupplier(request,id):
    quality=get_object_or_404(GreySuppliersMaster,id=id)
    q=request.POST.get("id")

    l=request.POST.get("supplier_name")
    # l = l.strip()

    m=request.POST.get("city")
    # m = m.strip()

    o=request.POST.get("email")
    # o = o.strip()

    p=request.POST.get("contact_number")
    # p = p.strip()

    r=request.POST.get("remarks") 
    # r = r.strip()  

    if q=="" or m=="" or o=="" or p=="" or r=="":
        messages.error(request,"please enter valid input")
        return redirect('/greyMasterSupplier')
    quality.id = q
    quality.supplier_name = l
    quality.city = m
    quality.email = o
    quality.contact_number = p
    quality.remarks = r
    quality.save()
    messages.success(request,"Supplier information edited")
    return redirect('/greyMasterSupplier')


##################################### GREY MASTER END ###########################################

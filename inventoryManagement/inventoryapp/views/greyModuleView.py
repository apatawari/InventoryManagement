from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,GreyQualityMaster,GreyCheckerMaster,GreyCutRange,ProcessingPartyNameMaster,GreyArrivalLocationMaster,ColorAndChemicalsSupplier,Color,ColorRecord,ChemicalsDailyConsumption,ChemicalsAllOrders,ChemicalsGodownLooseMergeStock,ChemicalsGodownsMaster,ChemicalsLooseGodownMaster,ChemicalsUnitsMaster,ChemicalsClosingStock
from inventoryapp.models import Employee,CompanyAccounts,ChemicalsClosingStockperGodown,MonthlyPayment,GreyTransportMaster,CityMaster,EmployeeCategoryMaster
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
                q_object=get_object_or_404(GreyQualityMaster,
                    qualities=data[6])
            except:
                q_object = GreyQualityMaster(
                    qualities=data[6]
                    )
                q_object.save()
            quality_object=get_object_or_404(GreyQualityMaster,qualities=data[6])
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
    qualities=GreyQualityMaster.objects.all().order_by('qualities')

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
    qualities=GreyQualityMaster.objects.all().order_by('qualities')
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
    qualities=GreyQualityMaster.objects.all().order_by('qualities')
    return render(request, './GreyModule/record.html', {'record':rec,'qualities':qualities})

###### GODOWN APPROVE FORM ######
def goDownApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    mindate=datetime.datetime.strptime(rec.bill_date,'%b %d,%Y').strftime('%Y-%m-%d')
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    qualities = GreyQualityMaster.objects.all()
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
    qualities=GreyQualityMaster.objects.all().order_by('qualities')
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
    qualities_all = GreyQualityMaster.objects.all().order_by('qualities')
    checkers=Employee.objects.all().order_by('name')
    transports=GreyTransportMaster.objects.all().order_by('transport')
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
    transport=get_object_or_404(GreyTransportMaster,id=t)

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

############ GREY: Checker(EMPLOYEE), Quality and Processing party master ##########
def renderAddChecker(request):
    all_checker = GreyCheckerMaster.objects.all().order_by('checker')
    #return render(request,'./GreyModule/addquality.html',{'allqualities':all_qualities})
    paginator = Paginator(all_checker,10)
    page = request.GET.get('page')
    checkers = paginator.get_page(page)

    return render(request,'./GreyModule/addchecker.html',{'records':checkers})

def saveChecker(request):
    q=request.POST.get("add_checker")
    q = q.strip()
    try:
        existing_quality=get_object_or_404(GreyCheckerMaster,checker=q.upper())
        messages.error(request,"This checker already exists")
    except:
        if q.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addchecker')
        new_quality = GreyCheckerMaster(
            checker=q.upper()
        )
        new_quality.save()
        messages.success(request,"Checker added")
    return redirect('/addchecker')

def deleteChecker(request,id):
    try:
        GreyCheckerMaster.objects.filter(id=id).delete()
        messages.success(request,"Checker deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addchecker')

def renderEditChecker(request,id):
    quality=get_object_or_404(GreyCheckerMaster,id=id)
    return render(request,'./GreyModule/editchecker.html',{'id':id,'name':quality.checker})

def editChecker(request,id):
    quality=get_object_or_404(GreyCheckerMaster,id=id)
    p=request.POST.get("edit-checker")
    p = p.upper()
    p = p.strip()
    quality.checker = p
    quality.save()
    messages.success(request,"Checker edited")
    return redirect('/addchecker')

######### GREY - CUT RANGE MASTER ########

def renderAddRange(request):
    all_checker = GreyCutRange.objects.all().order_by('range1')
    #return render(request,'./GreyModule/addquality.html',{'allqualities':all_qualities})
    paginator = Paginator(all_checker,10)
    page = request.GET.get('page')
    checkers = paginator.get_page(page)

    return render(request,'./GreyModule/addrate.html',{'records':checkers})

def saveRange(request):
    r1=float(request.POST.get("range_1"))
    r2=float(request.POST.get("range_2"))
    existingrange=GreyCutRange.objects.all()
    flag=0
    for i in existingrange:

        if i.range1<r1<i.range2 or i.range1<r2<i.range2:
            flag=flag+1
            break
    if flag==0:
        print("if")
        newR=GreyCutRange(
            range1=r1,
            range2=r2,
            rate=float(request.POST.get('rate'))
        )
        newR.save()
        messages.success(request,'Range added')
        return redirect('/addrate')

    else:
        print("else")
        messages.error(request,'Range collided')
        return redirect('/addrate')

def deleteRange(request,id):
    GreyCutRange.objects.filter(id=id).delete()
    messages.success(request,"Range deleted")
    return redirect('/addrate')


############ GREY : QUALITY MASTER ############

def renderAddQuality(request):
    all_qualities = GreyQualityMaster.objects.all().order_by('qualities')
    #return render(request,'./GreyModule/addquality.html',{'allqualities':all_qualities})
    paginator = Paginator(all_qualities,10)
    page = request.GET.get('page')
    qualities = paginator.get_page(page)

    return render(request,'./GreyModule/addquality.html',{'records':qualities})

def saveQuality(request):
    q=request.POST.get("newer_quality")
    q = q.strip()
    q=q.replace('"','inch')
    try:
        existing_quality=get_object_or_404(GreyQualityMaster,qualities=q.upper())
        messages.error(request,"This quality already exists")
    except:
        if q.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addquality')
        new_quality = GreyQualityMaster(
            qualities=q.upper()
        )
        new_quality.save()
        messages.success(request,"Quality added")
    return redirect('/addquality')

def deleteQuality(request,id):
    try:
        GreyQualityMaster.objects.filter(id=id).delete()
        messages.success(request,"Quality deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addquality')

def renderEditQuality(request,id):
    quality=get_object_or_404(GreyQualityMaster,id=id)
    return render(request,'./GreyModule/editquality.html',{'id':id,'name':quality.qualities})

def editQuality(request,id):
    quality=get_object_or_404(GreyQualityMaster,id=id)
    p=request.POST.get("edit-quality")
    p = p.upper()
    p = p.strip()
    quality.qualities = p
    quality.save()
    messages.success(request,"Grey Quality edited")
    return redirect('/addquality')

####### GREY : ARRIVAL LOCATION MASTER #######

def renderAddLocation(request):
    location_all = GreyArrivalLocationMaster.objects.all().order_by('location')
    #return render(request,'./GreyModule/addparty.html',{'parties':parties_all})

    paginator = Paginator(location_all,10)
    page = request.GET.get('page')
    locations = paginator.get_page(page)
    return render(request,'./GreyModule/addlocation.html',{'records':locations})

def saveLocation(request):
    p = request.POST.get("location")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(GreyArrivalLocationMaster,location=p)
        messages.error(request,"This arrival location already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addarrivallocation')
        new_loc = GreyArrivalLocationMaster(
            location= p
        )
        new_loc.save()
        messages.success(request,"Arrival location added successfully")
    return redirect('/addarrivallocation')

def deleteLocation(request,id):
    try:
        GreyArrivalLocationMaster.objects.filter(id=id).delete()
        messages.success(request,"Arrival location deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addarrivallocation')

def renderEditLocation(request,id):
    loc=get_object_or_404(GreyArrivalLocationMaster,id=id)
    return render(request,'./GreyModule/editlocation.html',{'id':id,'name':loc.location})

def editArrivalLocation(request,id):
    party=get_object_or_404(GreyArrivalLocationMaster,id=id)
    p=request.POST.get("edit-location")
    p = p.upper()
    p = p.strip()
    party.location = p
    party.save()
    messages.success(request,"Arrival location edited")
    return redirect('/addarrivallocation')


###### GREY : Processing House Party Master #######

def renderAddParty(request):
    parties_all = ProcessingPartyNameMaster.objects.all().order_by('processing_party')
    #return render(request,'./GreyModule/addparty.html',{'parties':parties_all})

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./GreyModule/addparty.html',{'records':parties})

def saveParty(request):
    p = request.POST.get("processing-party")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(ProcessingPartyNameMaster,processing_party=p)
        messages.error(request,"This Processing Party already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addparty')
        new_Party = ProcessingPartyNameMaster(
            processing_party= p
        )
        new_Party.save()
        messages.success(request,"Processing Party added successfully")
    return redirect('/addparty')

def deleteProcessingParty(request,id):
    try:
        ProcessingPartyNameMaster.objects.filter(id=id).delete()
        messages.success(request,"Processing House Party deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addparty')

def renderEditParty(request,id):
    party=get_object_or_404(ProcessingPartyNameMaster,id=id)
    return render(request,'./GreyModule/editparty.html',{'id':id,'name':party.processing_party})

def editProcessingParty(request,id):
    party=get_object_or_404(ProcessingPartyNameMaster,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.processing_party = p
    party.save()
    messages.success(request,"Processing House Party edited")
    return redirect('/addparty')


########## Transport Agency Master ###########

def renderAddTransport(request):
    parties_all = GreyTransportMaster.objects.all().order_by('transport')
    #return render(request,'./GreyModule/addparty.html',{'parties':parties_all})

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./GreyModule/addtransport.html',{'records':parties})

def saveTransport(request):
    p = request.POST.get("transport")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(GreyTransportMaster,transport=p)
        messages.error(request,"This Transport Party already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addtransport')
        new_Party = GreyTransportMaster(
            transport= p,
            rate=float(request.POST.get('rate'))
        )
        new_Party.save()
        messages.success(request,"Transport Party added successfully")
    return redirect('/addtransport')

def deleteTransport(request,id):
    try:
        GreyTransportMaster.objects.filter(id=id).delete()
        messages.success(request,"Transport Party deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addtransport')

def renderEditTransport(request,id):
    party=get_object_or_404(GreyTransportMaster,id=id)
    return render(request,'./GreyModule/edittransport.html',{'id':id,'name':party.transport,'rate':party.rate})

def editTransport(request,id):
    party=get_object_or_404(GreyTransportMaster,id=id)
    p=request.POST.get("edit-transport")
    p = p.upper()
    p = p.strip()
    party.transport = p
    party.rate = float(request.POST.get('rate'))
    party.save()
    messages.success(request,"Transport Party edited")
    return redirect('/addtransport')

##################################### GREY MASTER END ###########################################

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
    qualities=GreyQualityMaster.objects.all().order_by('qualities')
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
    processing_parties = ProcessingPartyNameMaster.objects.all().order_by('processing_party')
    d=datetime.date.today()
    d=str(d)
    return render(request, './GreyModule/processingapprove.html', {'date':d,'record':rec,'parties':processing_parties,'mindate':mindate,'maxdate':maxdate})

def sendInProcess(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_to_process")
    than_recieved = int(than_recieved)
    process_type = request.POST.get("processing-type")
    party_id=int(request.POST.get("processing-party"))
    partyprocessing=get_object_or_404(ProcessingPartyNameMaster,id=party_id)
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
    qualities=GreyQualityMaster.objects.all().order_by('qualities')
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
    locations = GreyArrivalLocationMaster.objects.all().order_by('location')

    d=datetime.date.today()
    d=str(d)
    return render(request, './GreyModule/readypprove.html', {'date':d,'record':rec,'mindate':mindate,'maxdate':maxdate,'parties':locations})

def readyToPrint(request,id):
    prevRec = get_object_or_404(Record,id=id)
    loc_id = int(request.POST.get("arrival-location"))
    location = get_object_or_404(GreyArrivalLocationMaster,id=loc_id)
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
        prevRec.arrival_location = location
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
            arrival_location=location,
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
    processing_parties = ProcessingPartyNameMaster.objects.all().order_by('processing_party')
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
        selected_party_object=get_object_or_404(ProcessingPartyNameMaster,processing_party=selected_parties[0])
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
        selected_party_object=get_object_or_404(ProcessingPartyNameMaster,processing_party=selected_parties[0])
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
            # data_row=[l,totalthan,pendingthan,rec_lists,rate]
            # data_block.append(data_row)
        #return render(request,'./GreyModule/ledgerreport.html',{'data':data_block,'h1':h1,'h2':"",'lot_no':lot,'party':s})


# def generateReport1(request):
#     selected_states=['In Process','Ready to print']
#     selected_states_all=['Transit','Godown','Checked','In Process','Ready to print']
#     selected_parties=[]
#     partyname=[]
#     send_parties=[]

#     send_data=[]

#     parties= ProcessingPartyName.objects.all()
#     # qualities= Quality.objects.all()
#     lot=request.POST.get("lot_no")
#     if lot == "":
#         lot=None
#     else:
#         lot=int(lot)
#     print(lot)
#     # start_date=request.POST.get("start_date")
#     # start_date=datetime.datetime.strptime(str(start_date), '%Y-%m-%d').strftime('%b %d,%Y')
#     # end_date=request.POST.get("end_date")
#     # end_date=datetime.datetime.strptime(str(end_date), '%Y-%m-%d').strftime('%b %d,%Y')
# # jjjj
# ##  Date filter

#     records = Record.objects.all()
#     for rec in records:
#         if(rec.party_name in partyname):
#             pass
#         else:
#             partyname.append(rec.party_name)

#     for p in partyname:
#         if(request.POST.get(p)!=None):
#             send_parties.append(request.POST.get(p))

#     # for p in parties:
#     #     if(request.POST.get(p.processing_party)!=None):
#     #         selected_parties.append(request.POST.get(p.processing_party))
#     s = request.POST.get("checkbox")
#     if s!=None:
#         selected_parties.append(s)
#     print(selected_parties)
#     begin = request.POST.get("start_date")
#     end = request.POST.get("end_date")
#     if(begin!="" or end!=""):

#         begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
#         end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
#         selected_dates=[]

#     # selected_qualities=[]
#         next_day = begin
#         while True:
#             if next_day > end:
#                 break



#             selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
#             next_day += datetime.timedelta(days=1)



#         begin=begin.strftime("%d/%m/%Y")
#         end=datetime.datetime.strptime(str(end),"%Y-%m-%d").date().strftime("%d/%m/%Y")
#         if(lot==None):
#             if(selected_parties!=[] and send_parties!=[]):
#                 rec = Record.objects.filter(processing_party_name__in=selected_parties,party_name__in=send_parties,sent_to_processing_date__in=selected_dates).order_by('lot_no','')

#             elif(selected_parties!=[] and send_parties==[]):
#                 rec = Record.objects.filter(processing_party_name__in=selected_parties,sent_to_processing_date__in=selected_dates).order_by('lot_no')
#             elif(selected_parties==[] and send_parties!=[]):


#                 for s in send_parties:
#                     transit_than=0
#                     godown_than=0
#                     checked_than=0
#                     processing_than=0
#                     ready_than=0
#                     transit_mtrs=0
#                     godown_mtrs=0
#                     checked_mtrs=0
#                     processing_mtrs=0
#                     ready_mtrs=0
#                     send_list=[]
#                     rec = Record.objects.filter(party_name=s).order_by('lot_no')
#                     for r in rec:
#                         if(r.state=='Transit'):
#                             transit_mtrs=transit_mtrs+r.mtrs
#                             transit_than=transit_than+r.than
#                         elif(r.state=='Godown'):
#                             godown_mtrs=godown_mtrs+r.mtrs
#                             godown_than=godown_than+r.than
#                         elif(r.state=='In Process'):
#                             processing_mtrs=processing_mtrs+r.mtrs
#                             processing_than=processing_than+r.than
#                         elif(r.state=='Ready to print'):
#                             ready_mtrs=ready_mtrs+r.mtrs
#                             ready_than=ready_than+r.than
#                         else:
#                             checked_mtrs=checked_mtrs+r.mtrs
#                             checked_than=checked_than+r.than
#                     total_than = transit_than + godown_than + checked_than + processing_than + ready_than
#                     total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
#                     send_list=[s,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
#                     send_data.append(send_list)
#                 return render(request,'./GreyModule/reportparty.html',{'data':send_data,'party':selected_parties[0],'begin':begin,'end':end})
#             else:
#                 rec= Record.objects.filter(sent_to_processing_date__in=selected_dates,state__in=selected_states).order_by('lot_no')

#         else:

#             if(selected_parties!=[] and send_parties!=[]):
#                 rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties,sent_to_processing_date__in=selected_dates,party_name__in=send_parties) #bill_date__range=[start_date,end_date]
#             elif(selected_parties!=[] and send_parties==[]):
#                 rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties,sent_to_processing_date__in=selected_dates)
#             elif(selected_parties==[] and send_parties!=[]):


#                 for s in send_parties:
#                     transit_than=0
#                     godown_than=0
#                     checked_than=0
#                     processing_than=0
#                     ready_than=0
#                     transit_mtrs=0
#                     godown_mtrs=0
#                     checked_mtrs=0
#                     processing_mtrs=0
#                     ready_mtrs=0
#                     send_list=[]
#                     rec = Record.objects.filter(lot_no=lot,party_name=s)
#                     for r in rec:
#                         if(r.state=='Transit'):
#                             transit_mtrs=transit_mtrs+r.mtrs
#                             transit_than=transit_than+r.than
#                         elif(r.state=='Godown'):
#                             godown_mtrs=godown_mtrs+r.mtrs
#                             godown_than=godown_than+r.than
#                         elif(r.state=='In Process'):
#                             processing_mtrs=processing_mtrs+r.mtrs
#                             processing_than=processing_than+r.than
#                         elif(r.state=='Ready to print'):
#                             ready_mtrs=ready_mtrs+r.mtrs
#                             ready_than=ready_than+r.than
#                         else:
#                             checked_mtrs=checked_mtrs+r.mtrs
#                             checked_than=checked_than+r.than
#                     total_than = transit_than + godown_than + checked_than + processing_than + ready_than
#                     total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
#                     send_list=[s,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
#                     send_data.append(send_list)
#                 return render(request,'./GreyModule/reportparty.html',{'data':send_data,'party':selected_parties[0],'begin':begin,'end':end})
#             else:
#                 rec= Record.objects.filter(lot_no=lot,sent_to_processing_date__in=selected_dates,state__in=selected_states)
#                 if(len(rec) == 0):
#                     rec = Record.objects.filter(lot_no=lot)
#                     transit_than=0
#                     godown_than=0
#                     checked_than=0
#                     processing_than=0
#                     ready_than=0
#                     transit_mtrs=0
#                     godown_mtrs=0
#                     checked_mtrs=0
#                     processing_mtrs=0
#                     ready_mtrs=0
#                     send_list=[]
#                     for r in rec:
#                         if(r.state=='Transit'):
#                             transit_mtrs=transit_mtrs+r.mtrs
#                             transit_than=transit_than+r.than
#                         elif(r.state=='Godown'):
#                             godown_mtrs=godown_mtrs+r.mtrs
#                             godown_than=godown_than+r.than
#                         elif(r.state=='In Process'):
#                             processing_mtrs=processing_mtrs+r.mtrs
#                             processing_than=processing_than+r.than
#                         elif(r.state=='Ready to print'):
#                             ready_mtrs=ready_mtrs+r.mtrs
#                             ready_than=ready_than+r.than
#                         else:
#                             checked_mtrs=checked_mtrs+r.mtrs
#                             checked_than=checked_than+r.than
#                     total_than = transit_than + godown_than + checked_than + processing_than + ready_than
#                     total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
#                     send_list=[lot,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
#                     send_data = [send_list]
#                     return render(request, './GreyModule/reportlot.html',{'data':send_data,'begin':begin,'end':end})

#         try:
#             return render(request,'./GreyModule/report.html',{'records':rec,'send_parties':send_parties,'party':selected_parties[0],'begin':begin,'end':end })
#         except:
#             if lot!=None:
#                 return render(request,'./GreyModule/report.html',{'records':rec,'send_parties':send_parties,'party':"Lot no - "+str(lot),'begin':begin,'end':end })
#             else:
#                 return render(request,'./GreyModule/report.html',{'records':rec,'send_parties':send_parties,'party':"Date",'begin':begin,'end':end })


#     else:
#         print("no date")
#         if(lot==None):
#             print("lot none")
#             if(selected_parties!=[] and send_parties!=[]):
#                 rec = Record.objects.filter(processing_party_name__in=selected_parties,party_name__in=send_parties).order_by('lot_no')
#                 return render(request,'./GreyModule/reportall.html',{'records':rec,'party':selected_parties[0]})
#             elif(selected_parties!=[] and send_parties==[]):
#                 rec = Record.objects.filter(processing_party_name__in=selected_parties).order_by('lot_no')
#                 return render(request,'./GreyModule/reportparty.html',{'records':rec,'send_parties':send_parties,'party':selected_parties[0]})

#             elif(selected_parties==[] and send_parties!=[]):


#                 for s in send_parties:
#                     transit_than=0
#                     godown_than=0
#                     checked_than=0
#                     processing_than=0
#                     ready_than=0
#                     transit_mtrs=0
#                     godown_mtrs=0
#                     checked_mtrs=0
#                     processing_mtrs=0
#                     ready_mtrs=0
#                     send_list=[]
#                     rec = Record.objects.filter(party_name=s).order_by('lot_no')
#                     for r in rec:
#                         if(r.state=='Transit'):
#                             transit_mtrs=transit_mtrs+r.mtrs
#                             transit_than=transit_than+r.than
#                         elif(r.state=='Godown'):
#                             godown_mtrs=godown_mtrs+r.mtrs
#                             godown_than=godown_than+r.than
#                         elif(r.state=='In Process'):
#                             processing_mtrs=processing_mtrs+r.mtrs
#                             processing_than=processing_than+r.than
#                         elif(r.state=='Ready to print'):
#                             ready_mtrs=ready_mtrs+r.mtrs
#                             ready_than=ready_than+r.than
#                         else:
#                             checked_mtrs=checked_mtrs+r.mtrs
#                             checked_than=checked_than+r.than
#                     total_than = transit_than + godown_than + checked_than + processing_than + ready_than
#                     total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
#                     send_list=[s,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
#                     send_data.append(send_list)
#                 return render(request,'./GreyModule/reportparty.html',{'data':send_data,'party':selected_parties[0]})
#             else:
#                 rec= Record.objects.filter(state__in=selected_states).order_by('lot_no')

#         else:
#             print("got lot")
#             if(selected_parties!=[] and send_parties!=[]):
#                 rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties,party_name__in=send_parties) #bill_date__range=[start_date,end_date]
#             elif(selected_parties!=[] and send_parties==[]):
#                 rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties)
#                 return render(request,'./GreyModule/reportparty.html',{'records':rec,'send_parties':send_parties,'party':selected_parties[0]})

#             elif(selected_parties==[] and send_parties!=[]):


#                 for s in send_parties:
#                     transit_than=0
#                     godown_than=0
#                     checked_than=0
#                     processing_than=0
#                     ready_than=0
#                     transit_mtrs=0
#                     godown_mtrs=0
#                     checked_mtrs=0
#                     processing_mtrs=0
#                     ready_mtrs=0
#                     send_list=[]
#                     rec = Record.objects.filter(lot_no=lot,party_name=s)
#                     for r in rec:
#                         if(r.state=='Transit'):
#                             transit_mtrs=transit_mtrs+r.mtrs
#                             transit_than=transit_than+r.than
#                         elif(r.state=='Godown'):
#                             godown_mtrs=godown_mtrs+r.mtrs
#                             godown_than=godown_than+r.than
#                         elif(r.state=='In Process'):
#                             processing_mtrs=processing_mtrs+r.mtrs
#                             processing_than=processing_than+r.than
#                         elif(r.state=='Ready to print'):
#                             ready_mtrs=ready_mtrs+r.mtrs
#                             ready_than=ready_than+r.than
#                         else:
#                             checked_mtrs=checked_mtrs+r.mtrs
#                             checked_than=checked_than+r.than
#                     total_than = transit_than + godown_than + checked_than + processing_than + ready_than
#                     total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
#                     send_list=[s,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
#                     send_data.append(send_list)
#                 return render(request,'./GreyModule/reportparty.html',{'data':send_data,'party':selected_parties[0]})
#             else:
#                 rec= Record.objects.filter(lot_no=lot,state__in=selected_states)
#                 print("got here")
#                 if(len(rec) == 0):
#                     rec = Record.objects.filter(lot_no=lot)
#                     transit_than=0
#                     godown_than=0
#                     checked_than=0
#                     processing_than=0
#                     ready_than=0
#                     transit_mtrs=0
#                     godown_mtrs=0
#                     checked_mtrs=0
#                     processing_mtrs=0
#                     ready_mtrs=0
#                     send_list=[]
#                     for r in rec:
#                         if(r.state=='Transit'):
#                             transit_mtrs=transit_mtrs+r.mtrs
#                             transit_than=transit_than+r.than
#                         elif(r.state=='Godown'):
#                             godown_mtrs=godown_mtrs+r.mtrs
#                             godown_than=godown_than+r.than
#                         elif(r.state=='In Process'):
#                             processing_mtrs=processing_mtrs+r.mtrs
#                             processing_than=processing_than+r.than
#                         elif(r.state=='Ready to print'):
#                             ready_mtrs=ready_mtrs+r.mtrs
#                             ready_than=ready_than+r.than
#                         else:
#                             checked_mtrs=checked_mtrs+r.mtrs
#                             checked_than=checked_than+r.than
#                     total_than = transit_than + godown_than + checked_than + processing_than + ready_than
#                     total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
#                     send_list=[lot,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
#                     send_data = [send_list]
#                     return render(request, './GreyModule/reportlot.html',{'data':send_data,'party':selected_parties[0]})
#         try:
#             return render(request,'./GreyModule/report.html',{'records':rec,'send_parties':send_parties,'party':selected_parties[0]})
#         except:
#             if lot!=None:
#                 return render(request,'./GreyModule/reportparty.html',{'records':rec,'send_parties':send_parties,'party':"Lot no - "+str(lot)})
#             else:
#                 return render(request,'./GreyModule/reportparty.html',{'records':rec,'send_parties':send_parties,'party':"Date" })

#         #return render(request,'./GreyModule/report.html',{'records':rec,'send_parties':send_parties,'party':selected_parties[0]})



############## GREY - DEFECTIVE STOCK ###############
def showDefective(request):
    records_list=Record.objects.filter(state__in=['Defect- Transport defect','Defect- Manufacturing defect'])
    records_filter = RecordFilter(request.GET,queryset=records_list)
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    qualities=GreyQualityMaster.objects.all().order_by('qualities')
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
        # for q in qualities:
        #     recs=Record.objects.filter(checker=checker,checking_date__in=selected_dates,quality=q.qualities)
        #     than=0
        #     mtrs=0
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
                range=GreyCutRange.objects.filter(range1__lt=mt,range2__gt=mt).first()
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
    transport=GreyTransportMaster.objects.all().order_by('transport')
    return render(request,'./GreyModule/transportfilter.html',{'d':d,'checkers':transport})


def transportReport(request):
    t_id=int(request.POST.get('transport'))
    transport=get_object_or_404(GreyTransportMaster,id=t_id)
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

        # for r in recs:
        #     totalthans=totalthans+r.than

        #     l=[]
        #     l.append(r.quality.qualities)
        #     l.append(r.checking_date)
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
        #     l.append(r.lot_no)
        #     datalist.append(l)
        total.append(round(totalbales,2))
        total.append(round(totaltotal,2))

        begin = str(begin)
        end= str(end)
        display_begin=datetime.datetime.strptime(str(begin),"%Y-%m-%d").date().strftime("%d/%m/%Y")
        display_end=datetime.datetime.strptime(str(end),"%Y-%m-%d").date().strftime("%d/%m/%Y")
        return render(request,'./GreyModule/transportreport.html',{'records':datalist,'total':total,'t':transport.transport,'checker':transport.id,'begin':begin,'end':end,'display_begin':display_begin,'display_end':display_end})



################### QUALITY WISE REPORT ########################
def qualityReportFilter(request):
    qualities= GreyQualityMaster.objects.all().order_by('qualities')
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
    qualities= GreyQualityMaster.objects.all()
    selected_qualities=[]
    for q in qualities:

        if(request.POST.get(q.qualities)!=None):
            selected_qualities.append(request.POST.get(q.qualities))
            rec_transit=Record.objects.filter(state="Transit",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.qualities))))
            tally_than=0
            tally_mtrs=0
            total_than_in_transit=0
            total_mtrs_in_transit=0

            for r in rec_transit:
                total_than_in_transit=total_than_in_transit+r.than
                total_mtrs_in_transit=total_mtrs_in_transit+r.mtrs
            trthan=trthan+total_than_in_transit
            trmtrs=trmtrs+total_mtrs_in_transit

            rec_godown=Record.objects.filter(state="Godown",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.qualities))))
            total_than_in_godown=0
            total_mtrs_in_godown=0
            for r in rec_godown:
                total_than_in_godown=total_than_in_godown+r.than
                total_mtrs_in_godown=total_mtrs_in_godown+r.mtrs
            gothan=gothan+total_than_in_godown
            gomtrs=gomtrs+total_mtrs_in_godown

            rec_checked=Record.objects.filter(state="Checked",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.qualities))))
            total_than_in_checked=0
            total_mtrs_in_checked=0
            for r in rec_checked:
                total_than_in_checked=total_than_in_checked+r.than
                total_mtrs_in_checked=total_mtrs_in_checked+r.mtrs
            chthan=chthan+total_than_in_checked
            chmtrs=chmtrs+total_mtrs_in_checked

            rec_process=Record.objects.filter(state="In Process",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.qualities))))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            rec_ready=Record.objects.filter(state="Ready to print",quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.qualities))))
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
    party=ProcessingPartyNameMaster.objects.all().order_by('processing_party')
    qualities=GreyQualityMaster.objects.all().order_by('qualities')
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
    party_ob=get_object_or_404(ProcessingPartyNameMaster,id=party_id)
    final_qs=[]
    total_all=[]

    prthan=0
    prmtrs=0
    rethan=0
    remtrs=0
    tothan=0
    tomtrs=0

    qualities= GreyQualityMaster.objects.all().order_by('qualities')
    selected_qualities=[]
    for q in qualities:

        if(request.POST.get(q.qualities)!=None):
            selected_qualities.append(request.POST.get(q.qualities))

            if(begin!="" or end!=""):
                rec_process=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="In Process",processing_party_name=party_ob,quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.qualities))))
            else:
                rec_process=Record.objects.filter(state="In Process",processing_party_name=party_ob,quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.qualities))))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            if(begin!="" or end!=""):
                rec_ready=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="Ready to print",processing_party_name=party_ob,quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.qualities))))
            else:
                rec_ready=Record.objects.filter(state="Ready to print",processing_party_name=party_ob,quality=get_object_or_404(GreyQualityMaster,id=int(request.POST.get(q.qualities))))

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

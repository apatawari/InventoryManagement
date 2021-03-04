from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from .models import Record,GreyQualityMaster,GreyCheckerMaster,GreyCutRange,ProcessingPartyNameMaster,GreyArrivalLocationMaster,ColorAndChemicalsSupplier,Color,ColorRecord,ChemicalsDailyConsumption,ChemicalsAllOrders,ChemicalsGodownLooseMergeStock,ChemicalsGodownsMaster,ChemicalsLooseGodownMaster,ChemicalsUnitsMaster,ChemicalsClosingStock
from .models import Employee,CompanyAccounts,ChemicalsClosingStockperGodown,MonthlyPayment,GreyTransportMaster,CityMaster,EmployeeCategoryMaster
from .resources import ItemResources
from .filters import RecordFilter,ColorFilter,ColorOrderFilter,GodownLeaseFilter,EmployeeFilter
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


####### EVENT HANDLERS ########
# Bad Request 400
def bad_request(request, exception):
    response = render('./error/400.html', context_instance=RequestContext(request))
    response.status_code = 400

    return response

# Permission Denied 403
def permission_denied(request, exception):
    response = render('./error/403.html', context_instance=RequestContext(request))
    response.status_code = 403

    return response

# Page Not Found 404
def page_not_found(request, exception):
    response = render('./error/404.html', context_instance=RequestContext(request))
    response.status_code = 404

    return response

# HTTP Error 500
def server_error(request):
    response = render('./error/500.html', context_instance=RequestContext(request))
    response.status_code = 500

    return response

###### GREY MODULE ######
##### HOMEPAGE #####
def index(request):
    recs=ChemicalsAllOrders.objects.all()
    idlist=[]
    for r in recs:
        try:
            dups=get_list_or_404(ChemicalsAllOrders,order_no=r.order_no,color=r.color,unit=r.unit,state="Ordered")
            flag=0
            for d in dups:
                if flag==0:
                    flag=1
                else:
                    idlist.append(d.id)

        except:
            pass

    colrecs=ColorRecord.objects.all()
    idlist2=[]
    for r in colrecs:
        try:
            dups=get_list_or_404(ColorRecord,order_no=r.order_no,color=r.color,unit=r.unit,state="Ordered")
            flag=0
            for d in dups:
                if flag==0:
                    flag=1
                else:
                    idlist2.append(d.id)

        except:
            pass

    for i in idlist:
        ChemicalsAllOrders.objects.filter(id=i).delete()
    for i in idlist2:
        ColorRecord.objects.filter(id=i).delete()

    return render(request, 'index.html')

def greyhome(request):
    return render(request, './GreyModule/greyhome.html')

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
        records_list=Record.objects.filter(state="In Process").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'checking_date', 'sent_to_processing_date', 'state', 'processing_type', 'processing_party_name__processing_party')
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
        records_list=Record.objects.filter(state="In Process").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'checking_date', 'sent_to_processing_date', 'state', 'processing_type', 'processing_party_name__processing_party')
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
        records_list=Record.objects.filter(state="In Process").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality__qualities', 'than', 'mtrs', 'rate', 'checking_date', 'sent_to_processing_date', 'state', 'processing_type', 'processing_party_name__processing_party')
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
                    trange=GreyCutRange.objects.filter(range1__lt=mt,range2__gt=mt).first()
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
            rec_transit=Record.objects.filter(state="Transit",quality=get_object_or_404(GreyQualityMaster,id=int(q)))
            tally_than=0
            tally_mtrs=0
            total_than_in_transit=0
            total_mtrs_in_transit=0

            for r in rec_transit:
                total_than_in_transit=total_than_in_transit+r.than
                total_mtrs_in_transit=total_mtrs_in_transit+r.mtrs
            trthan=trthan+total_than_in_transit
            trmtrs=trmtrs+total_mtrs_in_transit

            rec_godown=Record.objects.filter(state="Godown",quality=get_object_or_404(GreyQualityMaster,id=int(q)))
            total_than_in_godown=0
            total_mtrs_in_godown=0
            for r in rec_godown:
                total_than_in_godown=total_than_in_godown+r.than
                total_mtrs_in_godown=total_mtrs_in_godown+r.mtrs
            gothan=gothan+total_than_in_godown
            gomtrs=gomtrs+total_mtrs_in_godown

            rec_checked=Record.objects.filter(state="Checked",quality=get_object_or_404(GreyQualityMaster,id=int(q)))
            total_than_in_checked=0
            total_mtrs_in_checked=0
            for r in rec_checked:
                total_than_in_checked=total_than_in_checked+r.than
                total_mtrs_in_checked=total_mtrs_in_checked+r.mtrs
            chthan=chthan+total_than_in_checked
            chmtrs=chmtrs+total_mtrs_in_checked

            rec_process=Record.objects.filter(state="In Process",quality=get_object_or_404(GreyQualityMaster,id=int(q)))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            rec_ready=Record.objects.filter(state="Ready to print",quality=get_object_or_404(GreyQualityMaster,id=int(q)))
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
            qual=get_object_or_404(GreyQualityMaster,id=int(q))
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
        party_ob=get_object_or_404(ProcessingPartyNameMaster,processing_party=party_id)
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
                rec_process=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="In Process",processing_party_name=party_ob,quality=get_object_or_404(GreyQualityMaster,id=int(q)))
            else:
                rec_process=Record.objects.filter(state="In Process",processing_party_name=party_ob,quality=get_object_or_404(GreyQualityMaster,id=int(q)))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs
            prthan=prthan+total_than_in_process
            prmtrs=prmtrs+total_mtrs_in_process

            if(begin!="" or end!=""):
                rec_ready=Record.objects.filter(sent_to_processing_date__in=selected_dates,state="Ready to print",processing_party_name=party_ob,quality=get_object_or_404(GreyQualityMaster,id=int(q)))
            else:
                rec_ready=Record.objects.filter(state="Ready to print",processing_party_name=party_ob,quality=get_object_or_404(GreyQualityMaster,id=int(q)))

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

            d1=[get_object_or_404(GreyQualityMaster,id=int(q)).qualities,
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



###########################################     COLOR & CHEMICAL TAB   #################################################

####### COLOR - SUPPLIER MASTER ########
def renderAddColorSupplier(request):
    suppliers=ColorAndChemicalsSupplier.objects.all().order_by('supplier')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/colorsupplier.html',{'suppliers':parties})

def colorhome(request):
    return render(request, './ColorChemicalModule/colorhome.html')

def saveSupplier(request):
    p = request.POST.get("supplier")
    p = p.upper()
    p = p.strip()

    c = request.POST.get("city")
    c = c.upper()
    c = c.strip()

    a = request.POST.get("address")
    a = a.upper()
    a = a.strip()
    try:
        existing_party=get_object_or_404(ColorAndChemicalsSupplier,supplier=p,city=c,address=a)
        messages.error(request,"This Supplier Party already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addcolorsupplier')
        new_Party = ColorAndChemicalsSupplier(
            supplier = p,
            address=a,
            city=c
        )
        new_Party.save()
        messages.success(request,"Supplier Party added successfully")
    return redirect('/addcolorsupplier')

def deleteSupplier(request,id):
    try:
        ColorAndChemicalsSupplier.objects.filter(id=id).delete()
        messages.success(request,"Supplier Party deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addcolorsupplier')

def renderEditSupplier(request,id):
    party=get_object_or_404(ColorAndChemicalsSupplier,id=id)
    return render(request,'./ColorChemicalModule/editsupplier.html',{'id':id,'name':party.supplier})

def editSupplier(request,id):
    party=get_object_or_404(ColorAndChemicalsSupplier,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.supplier = p
    party.save()
    messages.success(request,"Supplier Party edited")
    return redirect('/addcolorsupplier')


#################### Color - ADD CHEMICAL/COLOR MASTER ################
def renderAddColor(request):
    suppliers=Color.objects.all().order_by('color')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/addcolor.html',{'suppliers':parties})

def saveColor(request):
    p = request.POST.get("color")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(Color,color=p)
        messages.error(request,"This Color already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addcolor')
        new_Party = Color(
            color = p
        )
        new_Party.save()
        messages.success(request,"Color added successfully")
    return redirect('/addcolor')

def deleteColor(request,id):
    try:
        Color.objects.filter(id=id).delete()
        messages.success(request,"Color deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addcolor')

def renderEditColor(request,id):
    party=get_object_or_404(Color,id=id)
    return render(request,'./ColorChemicalModule/editcolor.html',{'id':id,'name':party.color})

def editColor(request,id):
    party=get_object_or_404(Color,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.color = p
    party.save()
    messages.success(request,"Color edited")
    return redirect('/addcolor')

########### Add COLOR & CHEMICAL - Godown #############
def renderAddGodown(request):
    suppliers=ChemicalsGodownsMaster.objects.all().order_by('godown')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/addgodown.html',{'suppliers':parties})

def saveGodown(request):
    p = request.POST.get("godown")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(ChemicalsGodownsMaster,godown=p)
        messages.error(request,"This Godown already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addgodown')
        new_Party = ChemicalsGodownsMaster(
            godown = p
        )
        new_Party.save()
        messages.success(request,"Godown added successfully")
    return redirect('/addgodown')

def deleteGodown(request,id):
    try:
        ChemicalsGodownsMaster.objects.filter(id=id).delete()
        messages.success(request,"Godown deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addgodown')

def renderEditGodown(request,id):
    party=get_object_or_404(ChemicalsGodownsMaster,id=id)
    return render(request,'./ColorChemicalModule/editgodown.html',{'id':id,'name':party.godown})

def editGodown(request,id):
    party=get_object_or_404(ChemicalsGodownsMaster,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.godown = p
    party.save()
    messages.success(request,"Godown edited")
    return redirect('/addgodown')

########### Add COLOR & CHEMICAL - Loose Godown #############

def renderAddLease(request):
    suppliers=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/addlease.html',{'suppliers':parties})

def saveLease(request):
    p = request.POST.get("lease")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(ChemicalsLooseGodownMaster,lease=p)
        messages.error(request,"This Loose already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addlease')
        new_Party = ChemicalsLooseGodownMaster(
            lease = p
        )
        new_Party.save()
        messages.success(request,"Lease added successfully")
    return redirect('/addlease')

def deleteLease(request,id):
    try:
        ChemicalsLooseGodownMaster.objects.filter(id=id).delete()
        messages.success(request,"Lease deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addlease')

def renderEditLease(request,id):
    party=get_object_or_404(ChemicalsLooseGodownMaster,id=id)
    return render(request,'./ColorChemicalModule/editlease.html',{'id':id,'name':party.lease})

def editLease(request,id):
    party=get_object_or_404(ChemicalsLooseGodownMaster,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.lease = p
    party.save()
    messages.success(request,"Loose edited")
    return redirect('/addlease')


########### ADD COLOR & CHEMICAL - UNIT MASTER #############
def renderAddUnit(request):
    suppliers=ChemicalsUnitsMaster.objects.all().order_by('unit')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/addunit.html',{'suppliers':parties})

def saveUnit(request):
    p = request.POST.get("unit")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(ChemicalsUnitsMaster,unit=p)
        messages.error(request,"This Unit already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addunit')
        new_Party = ChemicalsUnitsMaster(
            unit = p
        )
        new_Party.save()
        messages.success(request,"Unit added successfully")
    return redirect('/addunit')

def deleteUnit(request,id):
    try:
        ChemicalsUnitsMaster.objects.filter(id=id).delete()
        messages.success(request,"Unit deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addunit')

def renderEditUnit(request,id):
    party=get_object_or_404(ChemicalsUnitsMaster,id=id)
    return render(request,'./ColorChemicalModule/editunit.html',{'id':id,'name':party.unit})

def editUnit(request,id):
    party=get_object_or_404(ChemicalsUnitsMaster,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.unit = p
    party.save()
    messages.success(request,"Unit edited")
    return redirect('/addunit')

########### Place order for COLOR & CHEMICAL #############

def placeOrder(request):
    color=Color.objects.all().order_by("color")
    suppliers=ColorAndChemicalsSupplier.objects.all().order_by('supplier')
    units=ChemicalsUnitsMaster.objects.all().order_by('unit')

    d=datetime.date.today()
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    d=str(d)
    try:
        rec = ColorRecord.objects.all().order_by('-order_no')[0]
        order_no=rec.order_no + 1
    except:
        order_no = 1
    return render(request,'./ColorChemicalModule/placeorder.html',{'color':color,'suppliers':suppliers,'units':units,'date':d,'maxdate':maxdate,'orderno':order_no})

def saveOrder(request):
    color_unit=[]
    q=float(request.POST.get('quantity'))
    r=float(request.POST.get('rate'))
    a=round(q*r,2)
    new_order=ColorRecord(
        color=get_object_or_404(Color,id=int(request.POST.get('color'))),
        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
        order_no=request.POST.get('order_no'),
        order_date=str(request.POST.get('order_date')),
        rate=request.POST.get('rate'),
        amount=a,
        quantity=request.POST.get('quantity'),
        state="Ordered",
        recieving_date=None,
        total_quantity = request.POST.get('quantity'),
        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit')))
    )
    new_order.save()

    new_order=ChemicalsAllOrders(
        color=get_object_or_404(Color,id=int(request.POST.get('color'))),
        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
        order_no=request.POST.get('order_no'),
        order_date=str(request.POST.get('order_date')),
        rate=request.POST.get('rate'),
        amount=a,
        quantity=request.POST.get('quantity'),
        state="Ordered",
        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit'))),
        rem_quantity=request.POST.get('quantity')
    )
    new_order.save()
    l=[request.POST.get('color'),request.POST.get('unit')]
    color_unit.append(l)
    if(request.POST.get('rate2')!='' and request.POST.get('quantity2')!='' and request.POST.get('color2')!=''):
        q=float(request.POST.get('quantity2'))
        r=float(request.POST.get('rate2'))
        a=round(q*r,2)
        l=[request.POST.get('color2'),request.POST.get('unit2')]
        if l in color_unit:
            messages.error(request,"Color Repeated. Order placed partially till first color")
            return redirect('/placeorder')
        color_unit.append(l)
        new_order=ColorRecord(
            color=get_object_or_404(Color,id=int(request.POST.get('color2'))),
            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
            order_no=request.POST.get('order_no'),
            order_date=str(request.POST.get('order_date')),
            rate=request.POST.get('rate2'),
            amount=a,
            quantity=request.POST.get('quantity2'),
            state="Ordered",
            recieving_date=None,
            total_quantity = request.POST.get('quantity2'),
            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit2')))
        )
        new_order.save()

        new_order=ChemicalsAllOrders(
            color=get_object_or_404(Color,id=int(request.POST.get('color2'))),
            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
            order_no=request.POST.get('order_no'),
            order_date=str(request.POST.get('order_date')),
            rate=request.POST.get('rate2'),
            amount=a,
            quantity=request.POST.get('quantity2'),
            state="Ordered",
            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit2'))),
            rem_quantity=request.POST.get('quantity2')
        )
        new_order.save()

        if(request.POST.get('rate3')!='' and request.POST.get('quantity3')!='' and request.POST.get('color3')!=''):
            q=float(request.POST.get('quantity3'))
            r=float(request.POST.get('rate3'))
            a=round(q*r,2)
            l=[request.POST.get('color3'),request.POST.get('unit3')]
            if l in color_unit:
                messages.error(request,"Color Repeated. Order placed partially till second color")
                return redirect('/placeorder')
            color_unit.append(l)
            new_order=ColorRecord(
                color=get_object_or_404(Color,id=int(request.POST.get('color3'))),
                supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                order_no=request.POST.get('order_no'),
                order_date=str(request.POST.get('order_date')),
                rate=request.POST.get('rate3'),
                amount=a,
                quantity=request.POST.get('quantity3'),
                state="Ordered",
                recieving_date=None,
                total_quantity = request.POST.get('quantity3'),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit3')))
            )
            new_order.save()

            new_order=ChemicalsAllOrders(
                color=get_object_or_404(Color,id=int(request.POST.get('color3'))),
                supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                order_no=request.POST.get('order_no'),
                order_date=str(request.POST.get('order_date')),
                rate=request.POST.get('rate3'),
                amount=a,
                quantity=request.POST.get('quantity3'),
                state="Ordered",
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit3'))),
                rem_quantity=request.POST.get('quantity3')
            )
            new_order.save()

            if(request.POST.get('rate4')!='' and request.POST.get('quantity4')!='' and request.POST.get('color4')!=''):
                q=float(request.POST.get('quantity4'))
                r=float(request.POST.get('rate4'))
                a=round(q*r,2)
                l=[request.POST.get('color4'),request.POST.get('unit4')]
                if l in color_unit:
                    messages.error(request,"Color Repeated. Order placed partially till third color")
                    return redirect('/placeorder')
                color_unit.append(l)
                new_order=ColorRecord(
                    color=get_object_or_404(Color,id=int(request.POST.get('color4'))),
                    supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                    order_no=request.POST.get('order_no'),
                    order_date=str(request.POST.get('order_date')),
                    rate=request.POST.get('rate4'),
                    amount=a,
                    quantity=request.POST.get('quantity4'),
                    state="Ordered",
                    recieving_date=None,
                    total_quantity = request.POST.get('quantity4'),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit4')))
                )
                new_order.save()

                new_order=ChemicalsAllOrders(
                    color=get_object_or_404(Color,id=int(request.POST.get('color4'))),
                    supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                    order_no=request.POST.get('order_no'),
                    order_date=str(request.POST.get('order_date')),
                    rate=request.POST.get('rate4'),
                    amount=a,
                    quantity=request.POST.get('quantity4'),
                    state="Ordered",
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit4'))),
                    rem_quantity=request.POST.get('quantity4')
                )
                new_order.save()

                if(request.POST.get('rate5')!='' and request.POST.get('quantity5')!='' and request.POST.get('color5')!=''):
                    q=float(request.POST.get('quantity5'))
                    r=float(request.POST.get('rate5'))
                    a=round(q*r,2)
                    l=[request.POST.get('color5'),request.POST.get('unit5')]
                    if l in color_unit:
                        messages.error(request,"Color Repeated. Order placed partially till fourth color")
                        return redirect('/placeorder')
                    color_unit.append(l)
                    new_order=ColorRecord(
                        color=get_object_or_404(Color,id=int(request.POST.get('color5'))),
                        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                        order_no=request.POST.get('order_no'),
                        order_date=str(request.POST.get('order_date')),
                        rate=request.POST.get('rate5'),
                        amount=a,
                        quantity=request.POST.get('quantity5'),
                        state="Ordered",
                        recieving_date=None,
                        total_quantity = request.POST.get('quantity5'),
                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit5')))
                    )
                    new_order.save()

                    new_order=ChemicalsAllOrders(
                        color=get_object_or_404(Color,id=int(request.POST.get('color5'))),
                        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                        order_no=request.POST.get('order_no'),
                        order_date=str(request.POST.get('order_date')),
                        rate=request.POST.get('rate5'),
                        amount=a,
                        quantity=request.POST.get('quantity5'),
                        state="Ordered",
                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit5'))),
                        rem_quantity=request.POST.get('quantity5')
                    )
                    new_order.save()

                    if(request.POST.get('rate6')!='' and request.POST.get('quantity6')!='' and request.POST.get('color6')!=''):
                        q=float(request.POST.get('quantity6'))
                        r=float(request.POST.get('rate6'))
                        a=round(q*r,2)
                        l=[request.POST.get('color6'),request.POST.get('unit6')]
                        if l in color_unit:
                            messages.error(request,"Color Repeated. Order placed partially till fifth color")
                            return redirect('/placeorder')
                        color_unit.append(l)
                        new_order=ColorRecord(
                            color=get_object_or_404(Color,id=int(request.POST.get('color6'))),
                            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                            order_no=request.POST.get('order_no'),
                            order_date=str(request.POST.get('order_date')),
                            rate=request.POST.get('rate6'),
                            amount=a,
                            quantity=request.POST.get('quantity6'),
                            state="Ordered",
                            recieving_date=None,
                            total_quantity = request.POST.get('quantity6'),
                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit6')))
                        )
                        new_order.save()

                        new_order=ChemicalsAllOrders(
                            color=get_object_or_404(Color,id=int(request.POST.get('color6'))),
                            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                            order_no=request.POST.get('order_no'),
                            order_date=str(request.POST.get('order_date')),
                            rate=request.POST.get('rate6'),
                            amount=a,
                            quantity=request.POST.get('quantity6'),
                            state="Ordered",
                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit6'))),
                            rem_quantity=request.POST.get('quantity6')
                        )
                        new_order.save()

                        if(request.POST.get('rate7')!='' and request.POST.get('quantity7')!='' and request.POST.get('color7')!=''):
                            q=float(request.POST.get('quantity7'))
                            r=float(request.POST.get('rate7'))
                            a=round(q*r,2)
                            l=[request.POST.get('color7'),request.POST.get('unit7')]
                            if l in color_unit:
                                messages.error(request,"Color Repeated. Order placed partially till sixth color")
                                return redirect('/placeorder')
                            color_unit.append(l)
                            new_order=ColorRecord(
                                color=get_object_or_404(Color,id=int(request.POST.get('color7'))),
                                supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                order_no=request.POST.get('order_no'),
                                order_date=str(request.POST.get('order_date')),
                                rate=request.POST.get('rate7'),
                                amount=a,
                                quantity=request.POST.get('quantity7'),
                                state="Ordered",
                                recieving_date=None,
                                total_quantity = request.POST.get('quantity7'),
                                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit7')))
                            )
                            new_order.save()

                            new_order=ChemicalsAllOrders(
                                color=get_object_or_404(Color,id=int(request.POST.get('color7'))),
                                supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                order_no=request.POST.get('order_no'),
                                order_date=str(request.POST.get('order_date')),
                                rate=request.POST.get('rate7'),
                                amount=a,
                                quantity=request.POST.get('quantity7'),
                                state="Ordered",
                                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit7'))),
                                rem_quantity=request.POST.get('quantity7')

                            )
                            new_order.save()

                            if(request.POST.get('rate8')!='' and request.POST.get('quantity8')!='' and request.POST.get('color8')!=''):
                                q=float(request.POST.get('quantity8'))
                                r=float(request.POST.get('rate8'))
                                a=round(q*r,2)
                                l=[request.POST.get('color8'),request.POST.get('unit8')]
                                if l in color_unit:
                                    messages.error(request,"Color Repeated. Order placed partially till seventh color")
                                    return redirect('/placeorder')
                                color_unit.append(l)
                                new_order=ColorRecord(
                                    color=get_object_or_404(Color,id=int(request.POST.get('color8'))),
                                    supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                    order_no=request.POST.get('order_no'),
                                    order_date=str(request.POST.get('order_date')),
                                    rate=request.POST.get('rate8'),
                                    amount=a,
                                    quantity=request.POST.get('quantity8'),
                                    state="Ordered",
                                    recieving_date=None,
                                    total_quantity = request.POST.get('quantity8'),
                                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit8')))
                                )
                                new_order.save()

                                new_order=ChemicalsAllOrders(
                                    color=get_object_or_404(Color,id=int(request.POST.get('color8'))),
                                    supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                    order_no=request.POST.get('order_no'),
                                    order_date=str(request.POST.get('order_date')),
                                    rate=request.POST.get('rate8'),
                                    amount=a,
                                    quantity=request.POST.get('quantity8'),
                                    state="Ordered",
                                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit8'))),
                                    rem_quantity=request.POST.get('quantity8')
                                )
                                new_order.save()

                                if(request.POST.get('rate9')!='' and request.POST.get('quantity9')!='' and request.POST.get('color9')!=''):
                                    q=float(request.POST.get('quantity9'))
                                    r=float(request.POST.get('rate9'))
                                    a=round(q*r,2)
                                    l=[request.POST.get('color9'),request.POST.get('unit9')]
                                    if l in color_unit:
                                        messages.error(request,"Color Repeated. Order placed partially till eight color")
                                        return redirect('/placeorder')
                                    color_unit.append(l)
                                    new_order=ColorRecord(
                                        color=get_object_or_404(Color,id=int(request.POST.get('color9'))),
                                        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                        order_no=request.POST.get('order_no'),
                                        order_date=str(request.POST.get('order_date')),
                                        rate=request.POST.get('rate9'),
                                        amount=a,
                                        quantity=request.POST.get('quantity9'),
                                        state="Ordered",
                                        recieving_date=None,
                                        total_quantity = request.POST.get('quantity9'),
                                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit9')))
                                    )
                                    new_order.save()

                                    new_order=ChemicalsAllOrders(
                                        color=get_object_or_404(Color,id=int(request.POST.get('color9'))),
                                        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                        order_no=request.POST.get('order_no'),
                                        order_date=str(request.POST.get('order_date')),
                                        rate=request.POST.get('rate9'),
                                        amount=a,
                                        quantity=request.POST.get('quantity9'),
                                        state="Ordered",
                                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit9'))),
                                        rem_quantity=request.POST.get('quantity9')
                                    )
                                    new_order.save()

                                    if(request.POST.get('rate10')!='' and request.POST.get('quantity10')!='' and request.POST.get('color10')!=''):
                                        q=float(request.POST.get('quantity10'))
                                        r=float(request.POST.get('rate10'))
                                        a=round(q*r,2)
                                        l=[request.POST.get('color10'),request.POST.get('unit10')]
                                        if l in color_unit:
                                            messages.error(request,"Color Repeated. Order placed partially till ninth color")
                                            return redirect('/placeorder')

                                        new_order=ColorRecord(
                                            color=get_object_or_404(Color,id=int(request.POST.get('color10'))),
                                            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                            order_no=request.POST.get('order_no'),
                                            order_date=str(request.POST.get('order_date')),
                                            rate=request.POST.get('rate10'),
                                            amount=a,
                                            quantity=request.POST.get('quantity10'),
                                            state="Ordered",
                                            recieving_date=None,
                                            total_quantity = request.POST.get('quantity10'),
                                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit10')))
                                        )
                                        new_order.save()

                                        new_order=ChemicalsAllOrders(
                                            color=get_object_or_404(Color,id=int(request.POST.get('color10'))),
                                            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                            order_no=request.POST.get('order_no'),
                                            order_date=str(request.POST.get('order_date')),
                                            rate=request.POST.get('rate10'),
                                            amount=a,
                                            quantity=request.POST.get('quantity10'),
                                            state="Ordered",
                                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit10'))),
                                            rem_quantity=request.POST.get('quantity10')
                                        )
                                        new_order.save()
    messages.success(request,'Order has been Placed')
    return redirect('/placeorder')

########### DISPLAY PLACED COLOR & CHEMICAL ORDERS #############
def orderGeneration(request):
    recs=ChemicalsAllOrders.objects.all()
    idlist=[]
    for r in recs:
        try:
            dups=get_list_or_404(ChemicalsAllOrders,order_no=r.order_no,color=r.color,unit=r.unit,state="Ordered")
            flag=0
            for d in dups:
                if flag==0:
                    flag=1
                else:
                    idlist.append(d.id)

        except:
            pass

    colrecs=ColorRecord.objects.all()
    idlist2=[]
    for r in colrecs:
        try:
            dups=get_list_or_404(ColorRecord,order_no=r.order_no,color=r.color,unit=r.unit,state="Ordered")
            flag=0
            for d in dups:
                if flag==0:
                    flag=1
                else:
                    idlist2.append(d.id)

        except:
            pass

    for i in idlist:
        ChemicalsAllOrders.objects.filter(id=i).delete()
    for i in idlist2:
        ColorRecord.objects.filter(id=i).delete()


    rec=ChemicalsAllOrders.objects.all().order_by('-state','order_no')
    records_filter = ColorOrderFilter(request.GET,queryset=rec)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    suppliers=ColorAndChemicalsSupplier.objects.all().order_by('supplier')
    colors=Color.objects.all().order_by('color')

    return render(request,'./ColorChemicalModule/ordergeneration.html',{'records':records,'filter':records_filter,'suppliers':suppliers,'colors':colors})

def orderEdit(request,id):
    rec=get_object_or_404(ChemicalsAllOrders, id=id)
    try:
        #rec2=get_object_or_404(ColorRecord,rate=rec.rate,order_no=rec.order_no,color=rec.color,unit=rec.unit,state="Ordered")

        orderdate=str(rec.order_date)
        color = Color.objects.all().order_by('color')
        supplier = ColorAndChemicalsSupplier.objects.all().order_by('supplier')
        unit = ChemicalsUnitsMaster.objects.all().order_by('unit')
        return render(request, './ColorChemicalModule/editorder.html',{'record':rec,'orderdate':orderdate,'color':color,'suppliers':supplier,'units':unit})
    except:
        messages.error(request,"This order has been recieved")
        return redirect('/ordergeneration')

def orderDelete(request,id):
    rec=get_object_or_404(ChemicalsAllOrders, id=id)
    rec2=get_object_or_404(ColorRecord,order_no=rec.order_no,color=rec.color,unit=rec.unit)
    rec.delete()
    rec2.delete()
    return redirect('/ordergeneration')

def orderEditSave(request,id):
    rec_order=get_object_or_404(ChemicalsAllOrders, id=id)
    q=float(request.POST.get('quantity'))
    r=float(request.POST.get('rate'))
    a=q*r
    a=round(a,2)
    orderno=rec_order.order_no
    color = rec_order.color
    unit=rec_order.unit
    rate=rec_order.rate
    try:
        rec=get_object_or_404(ColorRecord, rate=rate,order_no=orderno,color=color,unit=unit,state="Ordered")
        rec.supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier')))
        rec.color=get_object_or_404(Color,id=int(request.POST.get('color')))
        rec.order_date=str(request.POST.get('order_date'))
        rec.rate=request.POST.get('rate')
        rec.amount=a
        rec.quantity=request.POST.get('quantity')
        rec.total_quantity = request.POST.get('quantity')
        rec.unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit')))
        rec.save()
    finally:
        rec_order.supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier')))
        rec_order.color=get_object_or_404(Color,id=int(request.POST.get('color')))
        rec_order.order_date=str(request.POST.get('order_date'))
        rec_order.rate=request.POST.get('rate')
        rec_order.amount=a
        rec_order.quantity=request.POST.get('quantity')
        rec_order.rem_quantity=request.POST.get('quantity')
        rec_order.unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit')))
        rec_order.save()
    return redirect('/ordergeneration')


########### DISPLAY COLOR & CHEMICAL COMBINED STOCK IN GODOWN ############

def goodsReceived(request):
    godowns=ChemicalsGodownsMaster.objects.all()
    godowns_list=[]
    for g in godowns:
        godowns_list.append(g)

    godown_colors = ChemicalsGodownLooseMergeStock.objects.filter(state__in=godowns_list,loose_godown_state=None).exclude(quantity=0)
    # rec=ColorRecord.objects.filter(state='Godown').order_by('godown','color')
    records_filter = GodownLeaseFilter(request.GET,queryset=godown_colors)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    chemicals=Color.objects.all().order_by('color')
    godowns=ChemicalsGodownsMaster.objects.all().order_by('godown')

    return render(request,'./ColorChemicalModule/goodsreceived.html',{'filter':records_filter,'colors':records,'Godown':"Godown Containing",'chemicals':chemicals,'godowns':godowns})

def goodsRequest(request):
    rec=ColorRecord.objects.filter(state='Ordered').order_by('order_no')
    records_filter = ColorFilter(request.GET,queryset=rec)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request,'./ColorChemicalModule/goodsrequest.html',{'records':records,'filter':records_filter})

def goods(request,id):
    ogorder=get_object_or_404(ChemicalsAllOrders, id=id)
    rec=get_object_or_404(ColorRecord, order_no=ogorder.order_no,state="Ordered",color = ogorder.color, unit = ogorder.unit)

    mindate=str(rec.order_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    d=datetime.date.today()
    d=str(d)
    orderdate=str(rec.order_date)
    godowns = ChemicalsGodownsMaster.objects.all().order_by('godown')
    return render(request, './ColorChemicalModule/goodsapprove.html', {'date':d,'record':rec,'mindate':mindate,'maxdate':maxdate,'orderdate':orderdate,'godowns':godowns})

def viewOrder(request,id):
    ogorder = get_object_or_404(ChemicalsAllOrders, id=id)
    try:
        recieved_recs=get_list_or_404(ColorRecord, order_no=ogorder.order_no,state="Godown",color = ogorder.color, unit = ogorder.unit)
    except:
        recieved_recs=[]
    # mindate=str(rec.order_date)
    d=datetime.date.today().strftime('%Y-%m-%d')
    # d=.recieving_date
    d=str(d)
    orderdate=str(ogorder.order_date)
    billdate=str(ogorder.bill_date)
    godowns = ChemicalsGodownsMaster.objects.all().order_by('godown')
    print(billdate)
    remaining_order = 0

    for r in recieved_recs:

        remaining_order = remaining_order + r.quantity
    remaining_order = ogorder.quantity - remaining_order
    return render(request, './ColorChemicalModule/vieworder.html', {'d':d,'billdate':billdate,'record':ogorder,'orderdate':orderdate,'godowns':godowns,'recieved_recs':recieved_recs,'remaining':remaining_order})

######################### validate order ##########################
def renderValidate(request,id):
    rec=get_object_or_404(ChemicalsAllOrders, id=id)
    mindate=str(rec.order_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')


    return render(request, './ColorChemicalModule/validateorder.html', {'record':rec,'mindate':mindate,'maxdate':maxdate})

def validate(request,id):
    rec = get_object_or_404(ColorRecord,id=id)
    rec.bill_no=int(request.POST.get('billno'+str(rec.id)))
    rec.bill_date = request.POST.get('billdate'+str(rec.id))

    rec.save()
    all_recs = ColorRecord.objects.filter(order_no=rec.order_no,color=rec.color,unit=rec.unit).exclude(bill_date=None)
    q=0
    for i in all_recs:
        q=q+i.quantity
    ogorder=ChemicalsAllOrders.objects.filter(order_no=rec.order_no,color=rec.color,unit=rec.unit).first()
    if(q==ogorder.quantity):
        ogorder.validation="Yes"
        ogorder.save()

    messages.success(request,"Order Validated")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

#################### PLACED ORDERS TO GODOWN #######################
def goodsApprove(request,id):
    prevRec = get_object_or_404(ColorRecord,id=id)
    quantity_recieved = float(request.POST.get("quantityreceived"))
    g_id = int(request.POST.get('godownnumber'))
    godown=get_object_or_404(ChemicalsGodownsMaster,id=g_id)
    recieving_date = request.POST.get('receivingdate')
    recieve_date = datetime.datetime.strptime(recieving_date,'%Y-%m-%d').date()
    amount = prevRec.amount
    print(str(recieving_date))
    if(prevRec.quantity == quantity_recieved):
        prevRec.state="Godown"
        prevRec.recieving_date=str(recieving_date)
        prevRec.godown=godown
        prevRec.chalan_no=int(request.POST.get('chalan'))
        prevRec.recieving_date_string=str(recieving_date)
        prevRec.save()
        ogorder = get_object_or_404(ChemicalsAllOrders,order_no=prevRec.order_no,color=prevRec.color,unit=prevRec.unit)
        ogorder.state="Godown"
        ogorder.rem_quantity = 0
        ogorder.chalan_no=int(request.POST.get('chalan'))
        ogorder.save()
        try:


            try:
                try:
                    closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(godown=godown,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
                    closing_stock_pg.quantity=round(closing_stock_pg.quantity + quantity_recieved,2)
                    closing_stock_pg.save()

                except:
                    try:
                        closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(godown=godown,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                        pq=closing_stock_prev_pg.quantity
                    except:
                        pq=0
                    newpg= ChemicalsClosingStockperGodown(
                        color = get_object_or_404(Color,id=int(prevRec.color.id)),
                        quantity = round(pq + quantity_recieved,2),
                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                        rate = prevRec.rate,
                        dailydate = recieve_date,
                        godown=godown
                    )
                    newpg.save()
                #closing_stock = ClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit).order_by('-dailydate').first()
                closing_stock = ChemicalsClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()    ####loophole solved
                closing_stock.quantity=round(closing_stock.quantity + quantity_recieved,2)
                closing_stock.save()



            except:
                closing_stock_prev = ChemicalsClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()

                closing_stock= ChemicalsClosingStock(
                    color = get_object_or_404(Color,id=int(prevRec.color.id)),
                    quantity = round(closing_stock_prev.quantity + quantity_recieved,2),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                    rate = prevRec.rate,
                    dailydate = recieve_date
                )
                closing_stock.save()
            godown_color = get_object_or_404(ChemicalsGodownLooseMergeStock,color=prevRec.color,unit=prevRec.unit,state=godown)
            godown_color.quantity = round(godown_color.quantity + quantity_recieved,2)
            godown_color.rate = (godown_color.rate + prevRec.rate)/2
            godown_color.save()
        except:
            godown_color = ChemicalsGodownLooseMergeStock(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                state = godown
            )
            godown_color.save()
            closing_stock= ChemicalsClosingStock(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                dailydate = recieve_date
            )
            closing_stock.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/ordergeneration')
    elif(prevRec.quantity<quantity_recieved):
        messages.error(request,"Quantity Recieved cannot be more than Original Amount of Chemicals")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        quantity_remaining = round(prevRec.quantity - quantity_recieved)

        amount_per_quant = prevRec.amount/prevRec.quantity
        amount_recieved = amount_per_quant * quantity_recieved
        amount_remain = prevRec.amount - amount_recieved

        print(prevRec.color,prevRec.supplier,prevRec.unit,godown)
        color_ob=get_object_or_404(Color,id=int(prevRec.color.id))
        supp_ob=get_object_or_404(ColorAndChemicalsSupplier,id=int(prevRec.supplier.id))
        unit_ob=get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id))

        new_value = ColorRecord(
            recieving_date_string=str(recieving_date),
            recieving_date=str(recieving_date),
            color=color_ob,
            supplier=supp_ob,
            order_no=prevRec.order_no,
            order_date=prevRec.order_date,
            rate=prevRec.rate,
            amount=round(amount_recieved,2),
            quantity=quantity_recieved,
            unit = unit_ob,
            state="Godown",
            total_quantity = prevRec.total_quantity,
            godown = godown,
            chalan_no=int(request.POST.get('chalan')),


        )

        new_value.save()


        print(recieving_date)
        if quantity_recieved == 0 :
            messages.error(request,"Quantity Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:


            prevRec.quantity = round(prevRec.quantity - quantity_recieved,2)
            prevRec.amount = round(amount_remain,2)
            prevRec.save()
            ogorder = get_object_or_404(ChemicalsAllOrders,order_no=prevRec.order_no,color=prevRec.color,unit=prevRec.unit)
            ogorder.state="In Transit"
            ogorder.rem_quantity= round(ogorder.rem_quantity - quantity_recieved,2)
            ogorder.save()
            try:

                try:
                    try:
                        print("11")
                        closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(godown=godown,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
                        print("12")
                        closing_stock_pg.quantity=round(closing_stock_pg.quantity + quantity_recieved,2)
                        print("13")
                        closing_stock_pg.save()
                        print("14")

                    except:
                        try:
                            closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(godown=godown,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                            pq=closing_stock_prev_pg.quantity
                        except:
                            pq=0


                        newpg= ChemicalsClosingStockperGodown(
                            color = get_object_or_404(Color,id=int(prevRec.color.id)),
                            quantity = round(pq + quantity_recieved,2),
                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                            rate = prevRec.rate,
                            dailydate = recieve_date,
                            godown=godown
                        )
                        newpg.save()
                    closing_stock = ChemicalsClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
                    closing_stock.quantity=round(closing_stock.quantity + quantity_recieved,2)
                    closing_stock.save()
                    print("same rec",closing_stock.quantity)
                except:
                    closing_stock_prev = ChemicalsClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit,dailydate__lt=recieve_date).order_by('-dailydate').first()

                    closing_stock= ChemicalsClosingStock(
                        color = get_object_or_404(Color,id=int(prevRec.color.id)),
                        quantity = round(closing_stock_prev.quantity + quantity_recieved,2),
                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                        rate = prevRec.rate,
                        dailydate = recieve_date
                    )
                    closing_stock.save()
                    print("exc")

                godown_color = get_object_or_404(ChemicalsGodownLooseMergeStock,color=prevRec.color,unit=prevRec.unit,state=godown)
                godown_color.quantity = round(godown_color.quantity + quantity_recieved,2)
                godown_color.rate = (godown_color.rate + prevRec.rate)/2
                godown_color.save()
                print("godown")
            except:
                godown_color = ChemicalsGodownLooseMergeStock(
                    color = get_object_or_404(Color,id=int(prevRec.color.id)),
                    quantity = round(quantity_recieved,2),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                    rate = prevRec.rate,
                    state = godown
                )
                godown_color.save()
                closing_stock= ChemicalsClosingStock(
                    color = get_object_or_404(Color,id=int(prevRec.color.id)),
                    quantity = round(quantity_recieved,2),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                    rate = prevRec.rate,
                    dailydate = recieve_date
                )
                closing_stock.save()

            messages.success(request,"Data Updated Successfully")


        #print(than_in_transit,than_in_godown)
        return redirect('/ordergeneration')


# def htmltoText(html):
#     h=html2text.HTML2Text()
#     h.ignore_links=True
#     return h.handle(html)

################# Chemical in loose Godown ##################
def goodsLease(request):
    lease=ChemicalsLooseGodownMaster.objects.all()
    lease_list=[]
    for g in lease:
        lease_list.append(g)
    godown_colors = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state__in=lease_list,state=None).exclude(quantity=0).order_by('color')
    # rec=ColorRecord.objects.filter(state='Godown').order_by('godown','color')
    records_filter = GodownLeaseFilter(request.GET,queryset=godown_colors)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    # html = render_to_string('./ColorChemicalModule/lease.html',{'filter':records_filter,'colors':records})
    # text = htmltoText(html)
    # print(text)
    chemicals=Color.objects.all().order_by('color')
    loose_godowns=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request,'./ColorChemicalModule/lease.html',{'filter':records_filter,'colors':records,'chemicals':chemicals,'loose_godowns':loose_godowns})

def leaseRequest(request):
    godowns=ChemicalsGodownsMaster.objects.all()
    godowns_list=[]
    for g in godowns:
        godowns_list.append(g.godown)
    godown_colors = ChemicalsGodownLooseMergeStock.objects.filter(state__in=godowns_list).exclude(quantity=0)
    # rec=ColorRecord.objects.filter(state='Godown').order_by('godown','color')
    records_filter = GodownLeaseFilter(request.GET,queryset=godown_colors)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request,'./ColorChemicalModule/leaserequest.html',{'filter':records_filter,'colors':records})

def viewGood(request,id):
    rec=get_object_or_404(ChemicalsGodownLooseMergeStock, id=id)
    # mindate=str(rec.recieving_date)
    # maxdate=datetime.date.today().strftime('%Y-%m-%d')
    d=datetime.date.today()
    d=str(d)
    # recievedate=str(rec.recieving_date)
    lease = ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request, './ColorChemicalModule/leaseapprove.html', {'d':d,'record':rec,'lease':lease})


def leaseApprove(request,id):
    prevRec = get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)
    quantity_recieved = round(float(request.POST.get("quantitylease")),2)
    l_id = request.POST.get('leasenumber')
    loose_godown = get_object_or_404(ChemicalsLooseGodownMaster,id=int(l_id))
    recieve_date=datetime.datetime.strptime(request.POST.get('movingdate'),'%Y-%m-%d').date()
    if(prevRec.quantity == quantity_recieved):
        try:
            closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            print(closing_stock_g)
            closing_stock_g.quantity = round(closing_stock_g.quantity-quantity_recieved,2)
            print("sa")
            closing_stock_g.save()
        except:
            print("h1")
            closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
            print("h2")
            newpg= ChemicalsClosingStockperGodown(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(closing_stock_g.quantity -  quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                dailydate = recieve_date,
                godown=prevRec.state
            )
            newpg.save()
            print("h3")
        try:

            print("1")
            closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            print(closing_stock_pg)
            closing_stock_pg.quantity=round(closing_stock_pg.quantity + quantity_recieved,2)
            print("4")
            closing_stock_pg.save()
            print("5")

        except:
            print("here")
            # try:
            #     closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            #     closing_stock_g.quantity = round(closing_stock_g.quantity-quantity_recieved,2)
            #     closing_stock_g.save()
            # except:
            #     closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate_lt = recieve_date).order_by('-dailydate').first()
            #     newpg= ChemicalsClosingStockperGodown(
            #         color = get_object_or_404(Color,id=int(prevRec.color.id)),
            #         quantity = round(closing_stock_g.quantity -  quantity_recieved,2),
            #         unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
            #         rate = prevRec.rate,
            #         dailydate = recieve_date,
            #         godown=prevRec.state
            #     )
            #     newpg.save()
            try:
                closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                pq=closing_stock_prev_pg.quantity
            except:
                pq=0


            newpg= ChemicalsClosingStockperGodown(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(pq + quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                dailydate = recieve_date,
                loose_godown=loose_godown
                )
            newpg.save()
          ####################3
        try:
            godown_color = get_object_or_404(ChemicalsGodownLooseMergeStock,color=prevRec.color,unit=prevRec.unit,loose_godown_state=loose_godown)
            godown_color.quantity = round(godown_color.quantity + quantity_recieved,2)
            # r = round(((godown_color.rate + prevRec.rate)/2),2)
            # godown_color.rate=prevRec.rate
            godown_color.save()
        except:
            godown_color = ChemicalsGodownLooseMergeStock(
                color = prevRec.color,
                quantity = round(quantity_recieved,2),
                unit = prevRec.unit,
                rate = prevRec.rate,
                state = None,
                loose_godown_state=loose_godown
            )
            godown_color.save()
        prevRec.quantity=0
        prevRec.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/goodsreceived')
    elif(prevRec.quantity<quantity_recieved):
        messages.error(request,"Quantity Recieved cannot be more than Original Amount of Than")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        quantity_remaining = round(prevRec.quantity - quantity_recieved,2)
        try:
            try:
                print("21")
                closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
                print(closing_stock_g)
                closing_stock_g.quantity = round(closing_stock_g.quantity-quantity_recieved,2)
                print("23")
                closing_stock_g.save()
                print("24")
            except:
                closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                newpg= ChemicalsClosingStockperGodown(
                    color = get_object_or_404(Color,id=int(prevRec.color.id)),
                    quantity = round(closing_stock_g.quantity -  quantity_recieved,2),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                    rate = prevRec.rate,
                    dailydate = recieve_date,
                    godown=prevRec.state
                )
                newpg.save()
            closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            closing_stock_pg.quantity=round(closing_stock_pg.quantity + quantity_recieved,2)
            closing_stock_pg.save()


        except:
            # try:
            #     closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            #     closing_stock_g.quantity = round(closing_stock_g.quantity-quantity_recieved,2)
            #     closing_stock_g.save()
            # except:
            #     closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
            #     newpg= ChemicalsClosingStockperGodown(
            #         color = get_object_or_404(Color,id=int(prevRec.color.id)),
            #         quantity = round(closing_stock_g.quantity -  quantity_recieved,2),
            #         unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
            #         rate = prevRec.rate,
            #         dailydate = recieve_date,
            #         godown=prevRec.state
            #     )
            #     newpg.save()
            try:
                closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                pq=closing_stock_prev_pg.quantity
            except:
                pq=0


            newpg= ChemicalsClosingStockperGodown(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(pq + quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                dailydate = recieve_date,
                loose_godown=loose_godown
                )
            newpg.save()
        try:
            godown_color = get_object_or_404(ChemicalsGodownLooseMergeStock,color=prevRec.color,unit=prevRec.unit,loose_godown_state=loose_godown)
            godown_color.quantity = round(godown_color.quantity + quantity_recieved,2)
            # godown_color.rate = prevRec.rate

        except:
            godown_color = ChemicalsGodownLooseMergeStock(
                color = prevRec.color,
                quantity = round(quantity_recieved,2),
                unit = prevRec.unit,
                rate = prevRec.rate,
                state = None,
                loose_godown_state=loose_godown
            )

        if quantity_recieved == 0 :
            messages.error(request,"Quantity Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            prevRec.quantity=quantity_remaining
            prevRec.save()
            godown_color.save()
            messages.success(request,"Data Updated Successfully")


    return redirect('/goodsreceived')

def changeLooseGodown(request,id):
    leasestock = get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)
    #color = Color.objects.all().order_by('color')
    #units=ChemicalsUnitsMaster.objects.all().order_by('unit')
    #godowns=ChemicalsGodownsMaster.objects.all().order_by('godown')
    loose_godown=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request,'./ColorChemicalModule/editloosestocklg.html',{'record':leasestock,'loose':loose_godown})

def savechangeLooseGodown(request,id):
    if(float(request.POST.get('move-quantity'))==0):
        messages.error(request,"Please enter valid quantity")
        return redirect('/goodslease')
    l_id=request.POST.get('loosename')
    loose_object=get_object_or_404(ChemicalsLooseGodownMaster,id=int(l_id))
    move_quantity=round(float(request.POST.get('move-quantity')),2)

    merge_stock=get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)
    if(loose_object==merge_stock.loose_godown_state):
        messages.error(request,"Cannot update because loose godown you selected is same as previous")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    try:
        merge_stock_other=get_object_or_404(ChemicalsGodownLooseMergeStock,loose_godown_state=loose_object,color=merge_stock.color,unit=merge_stock.unit)
        merge_stock_other.quantity=round(merge_stock_other.quantity+move_quantity,2)
        merge_stock_other.save()
    except:
        new_merge_stock_other=ChemicalsGodownLooseMergeStock(
            color=merge_stock.color,
            unit=merge_stock.unit,
            quantity=move_quantity,
            rate=merge_stock.rate,
            state=None,
            loose_godown_state=loose_object
        )
        new_merge_stock_other.save()
    merge_stock.quantity=round(merge_stock.quantity - move_quantity)
    merge_stock.save()


    prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=merge_stock.loose_godown_state,color=merge_stock.color,unit=merge_stock.unit).order_by('-dailydate').first()
    prevlg.quantity = round(prevlg.quantity - move_quantity,2)
    prevlg.save()
    try:

        print("1")
        closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_object,color=merge_stock.color,unit=merge_stock.unit,dailydate=prevlg.dailydate).order_by('-dailydate').first()
        print(closing_stock_pg)
        closing_stock_pg.quantity=round(closing_stock_pg.quantity + move_quantity,2)
        print("4")
        closing_stock_pg.save()
        print("5")

    except:
        print("here")

        try:
            closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_object,color=merge_stock.color,unit=merge_stock.unit,dailydate__lt = prevlg.dailydate).order_by('-dailydate').first()
            pq=closing_stock_prev_pg.quantity
        except:
            pq=0


        newpg= ChemicalsClosingStockperGodown(
            color = get_object_or_404(Color,id=int(merge_stock.color.id)),
            quantity = round(pq + move_quantity,2),
            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(merge_stock.unit.id)),
            rate = merge_stock.rate,
            dailydate = prevlg.dailydate,
            loose_godown=loose_object
            )
        newpg.save()



    messages.success(request,"Loose godown name changed")
    return redirect('/goodslease')

def leaseedit(request,id):
    leasestock = get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)
    color = Color.objects.all().order_by('color')
    units=ChemicalsUnitsMaster.objects.all().order_by('unit')
    godowns=ChemicalsGodownsMaster.objects.all().order_by('godown')
    loose_godown=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request,'./ColorChemicalModule/editloosestock.html',{'record':leasestock,'color':color,'units':units,'loose':loose_godown,'godowns':godowns})

def savelease(request,id):
    g_id=request.POST.get('godownname')
    godown_object=get_object_or_404(ChemicalsGodownsMaster,id=int(g_id))
    act_quantity=round(float(request.POST.get('act-quantity')),2)

    stock=get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)

    old_quantity=stock.quantity
    diff=old_quantity-act_quantity
    if(diff<0):
        messages.error(request,"Please move extra quantity from godown section")
        return redirect('/goodsreceived')
    else:
        try:
            stockgodown=get_object_or_404(ChemicalsGodownLooseMergeStock,color=stock.color,unit=stock.unit,state=godown_object)
        except:
            messages.error(request,"Selected Godown never consisted this chemical")
            return redirect('/goodslease')
        stock.quantity=act_quantity
        stock.save()
        stockgodown.quantity=round(stockgodown.quantity+diff,2)
        stockgodown.save()

    prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=stock.loose_godown_state,color=stock.color,unit=stock.unit).order_by('-dailydate').first()
    prevlg.quantity = round(prevlg.quantity - diff,2)
    prevlg.save()

    prevgodown1 = ChemicalsClosingStockperGodown.objects.filter(godown=godown_object,color=stock.color,unit=stock.unit).order_by('-dailydate').first()
    prevgodown1.quantity = round(prevgodown1.quantity + diff)
    prevgodown1.save()

    messages.success(request,"Loose Godown quantity edited")
    return redirect('/goodslease')
########################### COLOR CHEMICAL LOOSE END ################################

########################### COLOR CHEMICAL DAILY CONSUMPTION ################################
def renderDailyConsumptionLease1(request):
    lease = ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    first_lease = ChemicalsLooseGodownMaster.objects.all().order_by('lease').first()
    try:
        color = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=first_lease.id).exclude(quantity=0).order_by('color')
    except:
        new_value = ChemicalsLooseGodownMaster(lease="Loose Godown 1")
        new_value.save()
        color = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=new_value.id).exclude(quantity=0).order_by('color')
    todays = ChemicalsDailyConsumption.objects.filter(con_date=str(datetime.date.today()))
    todaydate=str(datetime.date.today())
    return render(request,'./ColorChemicalModule/dailyconsumption.html',{'colors':color,'today':todaydate,'lease':lease,'name':first_lease.lease})

def renderDailyConsumptionLease2(request):
    l_id= request.POST.get('lease')
    loose_godown_object = get_object_or_404(ChemicalsLooseGodownMaster,id=int(l_id))
    leases = ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    color = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=loose_godown_object).exclude(quantity=0).order_by('color')
    todays = ChemicalsDailyConsumption.objects.filter(con_date=str(datetime.date.today()))
    todaydate=str(datetime.date.today())
    return render(request,'./ColorChemicalModule/dailyconsumption.html',{'colors':color,'today':todaydate,'lease':leases,'name':loose_godown_object.lease})

def backToDailyConsumption(request):
    return redirect('/dailyconsumptiondetails')

def dailyconsumptionDetails(request):
    l=ChemicalsLooseGodownMaster.objects.all().first()
    todays = ChemicalsDailyConsumption.objects.filter(con_date=str(datetime.date.today()),loose_godown=l).exclude(quantity=0)
    return render(request,'./ColorChemicalModule/dailyconsumptiondetails.html',{'records':todays,'d':str(datetime.date.today()),'date':str(datetime.date.today())})

def dailyconsumptionDetails2(request):
    date_c=request.POST.get('consumingdate')
    # date_c=datetime.datetime.strptime(date_c,"%Y-%m-%d").date()
    todays = ChemicalsDailyConsumption.objects.filter(con_date=date_c).exclude(quantity=0)
    return render(request,'./ColorChemicalModule/dailyconsumptiondetails.html',{'records':todays,'d':str(datetime.date.today()),'date':date_c})

def editDailyConsumption(request,id):
    rec=get_object_or_404(ChemicalsDailyConsumption,id=id)
    d=str(rec.con_date)
    return render(request,'./ColorChemicalModule/editdailyconsumption.html',{'record':rec,'d':d})

def saveDailyConsumption(request,id):
    rec=get_object_or_404(ChemicalsDailyConsumption,id=id)
    new_q=float(request.POST.get('new-quantity'))


    if(new_q>rec.quantity):
        messages.error(request,"Quantity cannot exceed original quantity")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    elif(new_q==rec.quantity):
        messages.error(request,"Quantity is same as original quantity")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    begin=datetime.datetime.strptime(str(rec.con_date),"%Y-%m-%d").date()
    end=datetime.date.today()
    selected_dates=[]

    # selected_qualities=[]
    next_day = begin
    while True:
        if next_day > end:
            break
        selected_dates.append((datetime.datetime.strptime(str(next_day), '%Y-%m-%d')))#.strftime('%b %d,%Y'))
        next_day += datetime.timedelta(days=1)

    #loose_godown_object=get_object_or_404(ChemicalsLooseGodownMaster,lease=rec.loose_godown.lease)
    #colors = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=loose_godown_object,).order_by('color')
    merge_color=get_object_or_404(ChemicalsGodownLooseMergeStock,color=rec.color,unit=rec.unit,loose_godown_state=rec.loose_godown)
    merge_color.quantity=round((merge_color.quantity + rec.quantity - new_q),2)
    merge_color.save()

    try:
        all_closingstocks=ChemicalsClosingStock.objects.filter(color=rec.color,unit=rec.unit,dailydate__in=selected_dates)

        for a in all_closingstocks:
            a.quantity=round((a.quantity + rec.quantity - new_q),2)
            a.save()


    except:
        pass

    try:
        all_prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=rec.loose_godown,color=rec.color,unit=rec.unit,dailydate__in=selected_dates).order_by('dailydate')

        for a in all_prevlg:

            a.quantity=round((a.quantity + rec.quantity - new_q),2)
            a.save()
    except:
        pass
    rec.quantity_remaining=round((rec.quantity_remaining+rec.quantity-new_q),2)
    rec.quantity=new_q

    rec.save()
    return redirect('/dailyconsumptiondetails')

######################## CONSUME STOCK FROM LOOSE GODOWN ######################
def consume(request,name):
    loose_godown_object=get_object_or_404(ChemicalsLooseGodownMaster,lease=name)
    colors = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=loose_godown_object).exclude(quantity=0).order_by('color')
    flag = 0
    consumingdate=request.POST.get('consumingdate')
    # print(consumingdate)
    # print(str(consumingdate))
    begin=datetime.datetime.strptime(consumingdate,"%Y-%m-%d").date()
    end=datetime.date.today()
    selected_dates=[]

    # selected_qualities=[]
    next_day = begin
    while True:
        if next_day > end:
            break
        selected_dates.append((datetime.datetime.strptime(str(next_day), '%Y-%m-%d')))#.strftime('%b %d,%Y'))
        next_day += datetime.timedelta(days=1)

    print(selected_dates)
    for c in colors:
        if(request.POST.get(str(c.id))==""):

            continue
        if(float(request.POST.get(str(c.id)))>c.quantity):
            flag = flag + 1
            continue

        try:
            prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown_object,color=c.color,unit=c.unit,dailydate__lte=str(consumingdate)).order_by('-dailydate').first()


            if(str(datetime.date.today()) != consumingdate):
                print("diff")
                all_prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown_object,color=c.color,unit=c.unit,dailydate__in=selected_dates).order_by('dailydate')

                for a in all_prevlg:
                    print("d")
                    a.quantity=round(a.quantity - float(request.POST.get(str(c.id))),2)
                    a.save()
                recbefore = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown_object,color=c.color,unit=c.unit,dailydate__in=selected_dates).order_by('-dailydate').first()
                if(str(datetime.date.today()) != str(recbefore.dailydate)):
                    new_lg = ChemicalsClosingStockperGodown(
                        color=c.color,
                        unit=c.unit,
                        quantity=recbefore.quantity,
                        dailydate=str(datetime.date.today()),
                        rate=c.rate,
                        loose_godown = loose_godown_object
                    )
                    new_lg.save()
            else:
                if(str(prevlg.dailydate)!=str(datetime.date.today())):
                    new_lg = ChemicalsClosingStockperGodown(
                        color=c.color,
                        unit=c.unit,
                        quantity=round((prevlg.quantity - float(request.POST.get(str(c.id)))),2),
                        dailydate=str(datetime.date.today()),
                        rate=c.rate,
                        loose_godown = loose_godown_object
                    )
                    new_lg.save()
                else:
                    prevlg.quantity = round(prevlg.quantity - float(request.POST.get(str(c.id))),2)
                    prevlg.save()

        except:
            pass
        try:
            closing_stock = ChemicalsClosingStock.objects.filter(color=c.color,unit=c.unit,dailydate__lte=str(consumingdate)).order_by('-dailydate').first()
            print(str(closing_stock.dailydate),closing_stock.quantity,type(closing_stock.dailydate))
            print(type(consumingdate))
            #closing_stock = ClosingStock.objects.filter(color=c.color,unit=c.unit).order_by('-dailydate').first()
            if(str(closing_stock.dailydate) != consumingdate):
                print("done4")
                new_cs = ChemicalsClosingStock(
                    color=c.color,
                    unit=c.unit,
                    quantity=round((closing_stock.quantity - float(request.POST.get(str(c.id)))),2),
                    dailydate=str(consumingdate),
                    rate=c.rate
                )
                new_cs.save()
            else:
                closing_stock.quantity=round((closing_stock.quantity - float(request.POST.get(str(c.id)))),2)
                closing_stock.save()
                print("done")
            new_dates=selected_dates[1:]


            all_closingstocks = ChemicalsClosingStock.objects.filter(color=c.color,unit=c.unit,dailydate__in=new_dates)
            #print("got all")
            #print(new_dates)
            for a in all_closingstocks:
                print(a.color)
                print(a.dailydate)
                a.quantity=round((a.quantity-float(request.POST.get(str(c.id)))),2)
                a.save()
        except:
            #print("ec")
            pass



        c.quantity=round((c.quantity - float(request.POST.get(str(c.id)))),2)
        c.save()
        stored_color = ChemicalsGodownLooseMergeStock.objects.filter(color=c.color,unit=c.unit)
        q=0
        for sc in stored_color:
            q=round((q+sc.quantity),2)

        daily_consump = ChemicalsDailyConsumption(
            con_date = str(consumingdate),
            color = c.color,
            unit = c.unit,
            quantity = round(float(request.POST.get(str(c.id))),2),
            quantity_remaining = q,
            loose_godown= loose_godown_object
        )
        daily_consump.save()

    if (flag != 0):
        messages.error(request,"%s Quantity entered exceeded the quantities available in Loose" %(flag))
    return redirect('/dailyconsumption1')


########################### DISPLAY CLOSING STOCK #############################
def renderClosingStock(request):
    godowns=ChemicalsGodownsMaster.objects.all()
    godowns_list=[]
    for g in godowns:
        godowns_list.append(g)

    lease=ChemicalsLooseGodownMaster.objects.all()
    lease_list=[]
    for l in lease:
        lease_list.append(l)

    datalist=[]
    colors=Color.objects.all()
    units=ChemicalsUnitsMaster.objects.all()
    for c in colors:
        for u in units:
            try:
                lq=0
                recsl=get_list_or_404(ChemicalsGodownLooseMergeStock,color=c,unit=u,loose_godown_state__in=lease_list)
                for i in recsl:
                    lq=lq+i.quantity

                recsg=get_list_or_404(ChemicalsGodownLooseMergeStock,color=c,unit=u,state__in=godowns_list,loose_godown_state=None)
                lg=0
                for i in recsg:
                    lg=lg+i.quantity
                l=[]
                l.append(c.color)
                l.append(u.unit)
                l.append(lq)
                l.append(lg)
                l.append(round(lq+lg,2))
                datalist.append(l)
            except:
                try:
                    recsg=get_list_or_404(ChemicalsGodownLooseMergeStock,color=c,unit=u,state__in=godowns_list,loose_godown_state=None)

                    lg=0
                    for i in recsg:
                        lg=lg+i.quantity
                    l=[]
                    l.append(c.color)
                    l.append(u.unit)
                    l.append(0)
                    l.append(lg)
                    l.append(lg)
                    datalist.append(l)

                except:
                    pass


    return render(request,'./ColorChemicalModule/closingstock.html',{'colors':datalist})

########################### COLOR REPORT FILTER #################################
def renderColorReportFilter(request):
    d=str(datetime.date.today())
    godowns = ChemicalsGodownsMaster.objects.all().order_by('godown')
    loose_godowns=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request,'./ColorChemicalModule/reportfilter.html',{'d':d,'godowns':godowns,'loose':loose_godowns})

# def colorReport(request):
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
#     datalist=[]
#     colors= Color.objects.all()
#     units= Units.objects.all()
#     for c in colors:
#         for u in units:
#             try:
#                 records=get_list_or_404(DailyConsumption,con_date__in=selected_dates,color=c.color,unit=u.unit)
#                 l=[]
#                 quantity = 0
#                 for rec in records:
#                     quantity = quantity+rec.quantity
#                 l.append(c.color)
#                 l.append(u.unit)

#                 try:
#                     first_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[0],color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 except:
#                     first_record = ClosingStock.objects.filter(color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 try:
#                     last_record = get_object_or_404(ClosingStock,dailydate=selected_dates[-1],color = c.color,unit = u.unit)
#                 except:
#                     last_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[-1],color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 l.append(first_record.quantity)
#                 l.append(quantity)
#                 l.append(last_record.quantity)
#                 datalist.append(l)
#                 print(first_record.quantity,first_record.con_date)
#             except:
#                 l=[]
#                 l.append(c.color)
#                 l.append(u.unit)

#                 try:
#                     first_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[0],color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 except:
#                     first_record = ClosingStock.objects.filter(color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 try:
#                     last_record = get_object_or_404(ClosingStock,dailydate=selected_dates[-1],color = c.color,unit = u.unit)
#                 except:
#                     last_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[-1],color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 l.append(0)
#                 l.append(0)
#                 l.append(0)
#                 datalist.append(l)

#     return render(request,'./ColorChemicalModule/report.html',{'data':datalist,'begin':begin,'end':end})


########### previous working color report

# def colorReport(request):
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
#                 new_stock=0
#                 try:

#                     #neworders = get_list_or_404(ColorRecord,recieving_date__in=selected_dates,color=c,unit=u)
#                     neworders=ColorRecord.objects.filter(recieving_date__in=selected_dates,color=c,unit=u)
#                     print(neworders)
#                     for i in neworders:

#                         new_stock=new_stock+i.quantity

#                 except:
#                     pass

#                 l.append(new_stock)
#                 datalist.append(l)
#                 # print(first_record.quantity,first_record.con_date)
#             except:
#                 pass
#     begin=str(begin)
#     end=str(end)
#     display_begin=datetime.datetime.strptime(str(begin),"%Y-%m-%d").date().strftime("%d/%m/%Y")
#     display_end=datetime.datetime.strptime(str(end),"%Y-%m-%d").date().strftime("%d/%m/%Y")
#     return render(request,'./ColorChemicalModule/report.html',{'data':datalist,'begin':begin,'end':end, 'display_begin': display_begin, 'display_end': display_end})

########################### COLOR REPORT MAIN FUNCTION #################################
def colorReport(request):
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

    selected_godowns=[]
    selected_loose=[]
    selected_godowns_id=[]
    selected_loose_id=[]
    for g in godowns:
        if(request.POST.get(g.godown)!=None):
            selected_godowns.append(get_object_or_404(ChemicalsGodownsMaster,id=int(request.POST.get(g.godown))))
            selected_godowns_id.append(int(request.POST.get(g.godown)))
    for g in loose_godowns:
        if(request.POST.get(g.lease)!=None):
            selected_loose.append(get_object_or_404(ChemicalsLooseGodownMaster,id=int(request.POST.get(g.lease))))
            selected_loose_id.append(int(request.POST.get(g.lease)))

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

    ######################### opening stock ##################################
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

###################### new stock #################################
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

################################# consumption ########################################
                if selected_godowns!=[] and selected_loose==[]:
                    l.append("loop")
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
############################### closing stock ##############################
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
    begin=str(begin)
    end=str(end)
    display_begin=datetime.datetime.strptime(str(begin),"%Y-%m-%d").date().strftime("%d/%m/%Y")
    display_end=datetime.datetime.strptime(str(end),"%Y-%m-%d").date().strftime("%d/%m/%Y")
    return render(request,'./ColorChemicalModule/report.html',{'data':datalist,'begin':begin,'end':end, 'display_begin': display_begin, 'display_end': display_end,'selected_godowns_id':selected_godowns_id,'selected_loose_id':selected_loose_id})



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
    n = n.strip()

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

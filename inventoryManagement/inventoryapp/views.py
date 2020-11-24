from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from .models import Record,Quality,ProcessingPartyName,ArrivalLocation,ColorSupplier,Color,ColorRecord,DailyConsumption,AllOrders,GodownLeaseColors,Godowns,Lease,Units,ClosingStock
from .resources import ItemResources
from .filters import RecordFilter,ColorFilter,ColorOrderFilter,GodownLeaseFilter
from django.contrib import messages
from tablib import Dataset
from django.http import HttpResponseRedirect
import pandas
import numpy as np
import datetime
import xlwt
from django.template.loader import render_to_string



#from django.shortcuts import render_to_response


# Bad Request 400
def bad_request(request, exception):
    response = render('400.html', context_instance=RequestContext(request))
    response.status_code = 400

    return response

# Permission Denied 403
def permission_denied(request, exception):
    response = render('403.html', context_instance=RequestContext(request))
    response.status_code = 403

    return response

# Page Not Found 404
def page_not_found(request, exception):
    response = render('404.html', context_instance=RequestContext(request))
    response.status_code = 404

    return response

# HTTP Error 500
def server_error(request):
    response = render('500.html', context_instance=RequestContext(request))
    response.status_code = 500

    return response

def index(request):
    return render(request, 'index.html')

def greyhome(request):
    return render(request, 'greyhome.html')

def back1(request):
    return redirect('/intransit')

def back2checking(request):
    return redirect('/checking')
# def back2processing(request):
#     return redirect('/inprocess')
# def back2ready(request):
#     return redirect('/readytoprint')


def back(request,state):
    print(state)
    if state == "Transit":
        return redirect('/godownrequest')
    elif state == "Godown":
        return redirect('/checkingrequest')
    elif state == "Checked":
        return redirect('/processingrequest')
    elif state == "In Process":
        return redirect('/readytoprintrequest')
    

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

            imported_data = dataset.load(excel_data_df)
            # result = item_resource.import_data(dataset, dry_run=True)
            # print(imported_data)
        except:
            messages.error(request, "Please Select Proper File")
            return redirect('/greyhome')
            
        for data in imported_data:
            try:
                
                rec=get_list_or_404(Record, 
                    party_name=data[1],
                    bill_no=data[2],
                    bill_amount=data[4],
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
                    quality=data[6],
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
                try:
                    rec=get_object_or_404(Quality,
                        qualities=data[6])
                except:
                    new_quality = Quality(
                        qualities=data[6]
                        )
                    new_quality.save()
                try:
                    rec=get_object_or_404(ColorSupplier,
                        supplier=data[1])
                except:
                    new_sup = ColorSupplier(
                        supplier=data[1]
                        )
                    new_sup.save()
        if (counter > 0):
            messages.success(request,str(counter)+ " Records were Inserted")
        else:
            messages.error(request, "These records already exist")


    return redirect('/greyhome')

def showIntransit(request):
    records_list=Record.objects.filter(state="Transit").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
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

    return render(request, 'intransit.html',{'records':records,'filter':records_filter,'sums':sums})
    

def showGodown(request):
    records_list=Record.objects.filter(state="Godown").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
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
    return render(request, 'godown.html',{'records':records,'filter':records_filter,'sums':sums})

def showGodownRequest(request):
    records_list=Record.objects.filter(state="Transit").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'godownrequest.html',{'records':records,'filter':records_filter})

def record(request,id):
    rec=get_object_or_404(Record, id=id)
    return render(request, 'record.html', {'record':rec})

def goDownApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    mindate=datetime.datetime.strptime(rec.bill_date,'%b %d,%Y').strftime('%Y-%m-%d')
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    qualities = Quality.objects.all()
    d=datetime.date.today()
    d=str(d)
    return render(request, 'godownapprove.html', {'record':rec,'qualities':qualities,'mindate':mindate,'maxdate':maxdate,'date':d})

def edit(request,id):
    if request.method=="POST":
        record = get_object_or_404(Record,id=id)
        prevBale=record.bale
        record.party_name=request.POST.get("party_name")
        record.bill_no=request.POST.get("bill_no")
        record.bill_date=request.POST.get("bill_date")
        record.bill_amount=request.POST.get("bill_amount")
        record.lot_no=request.POST.get("lot_no")
        record.quality=request.POST.get("quality")
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
        # records=Record.objects.all()
        
        # return render(request,'intransit.html',{'records':records})
        
# def searchIntransit(request):
#     records_list=Record.objects.all()
#     records_filter = RecordFilter(request.GET,queryset=records_list)
#     return render(request,'intransit.html',{'records':records_filter})
#?page={{records.next_page_number}}

def nextRec(request,id):
    rec=get_object_or_404(Record, id=id+1)
    return render(request, 'record.html', {'record':rec})

def prevRec(request,id):
    rec=get_object_or_404(Record, id=id-1)
    return render(request, 'record.html', {'record':rec})

#Intransit To Godown
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
        return redirect('/godownrequest')
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
        return redirect('/godownrequest')

#quality2 = request.POST.get("quality2")

def showChecked(request):
    records_list=Record.objects.filter(state="Checked").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
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

    return render(request, 'checking.html',{'records':records,'filter':records_filter,'sums':sums})

def showCheckingRequest(request):
    records_list=Record.objects.filter(state="Godown").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'checkingrequest.html',{'records':records,'filter':records_filter})

def checkingApprove(request,id):
    rec=get_object_or_404(Record, id=id)

    mindate=str(rec.recieving_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    qualities_all = Quality.objects.all().order_by('qualities')
    d=datetime.date.today()
    d=str(d)
    return render(request, 'checkingapprove.html', {'date':d,'record':rec,'qualities':qualities_all,'mindate':mindate,'maxdate':maxdate})

def approveCheck(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_recieved")
    than_recieved = int(than_recieved)
    defect=request.POST.get("defect")
    mtrs_edit=request.POST.get("mtrs-checked")
    
    
    total_amount=prevRec.bill_amount
    totalthan=prevRec.than
    cost_per_than=total_amount/totalthan
    cost_per_than=round(cost_per_than,2)
    if(defect=="no defect"):
    
        if(prevRec.than == than_recieved):
            prevRec.state="Checked"
            prevRec.quality=request.POST.get("new-quality")
            prevRec.checking_date=str(request.POST["checking_date"])
            if(mtrs_edit==""):
                mtrs_edit=prevRec.mtrs
            prevRec.mtrs=mtrs_edit
            prevRec.save()
            messages.success(request,"Data Updated Successfully")
            return redirect('/checkingrequest')
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
                quality=request.POST.get("new-quality"),
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
                checking_date=str(request.POST["checking_date"])
            
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
            prevRec.quality=request.POST.get("new-quality")
            prevRec.checking_date=str(request.POST["checking_date"])
            if(mtrs_edit==""):
                mtrs_edit=prevRec.mtrs
            prevRec.mtrs=mtrs_edit
            prevRec.save()
            messages.success(request,"Data updated to defective state")

            return redirect('/checkingrequest')
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
                quality=request.POST.get("new-quality"),
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
                checking_date=str(request.POST["checking_date"])
            
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

    return redirect('/checkingrequest')

def editChecked(request,id):
    rec=get_object_or_404(Record, id=id)
    return render(request, 'editchecked.html', {'record':rec})


def checkedEdit(request,id):
    if request.method=="POST":
        record = get_object_or_404(Record,id=id)
        record.party_name=request.POST.get("party_name")
        record.bill_no=request.POST.get("bill_no")
        record.bill_date=request.POST.get("bill_date")
        record.bill_amount=request.POST.get("bill_amount")
        record.lot_no=request.POST.get("lot_no")
        record.quality=request.POST.get("quality")
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

#Quality and Processing part master
def renderAddQuality(request):
    all_qualities = Quality.objects.all().order_by('qualities')
    #return render(request,'addquality.html',{'allqualities':all_qualities})
    paginator = Paginator(all_qualities,10)
    page = request.GET.get('page')
    qualities = paginator.get_page(page)

    return render(request,'addquality.html',{'records':qualities})

def saveQuality(request):
    q=request.POST.get("newer_quality")
    q = q.strip()
    try:
        existing_quality=get_object_or_404(Quality,qualities=q.upper())
        messages.error(request,"This quality already exists")
    except:
        if q.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addquality')
        new_quality = Quality(
            qualities=q.upper()
        )
        new_quality.save()
        messages.success(request,"Quality added")
    return redirect('/addquality')

def deleteQuality(request,id):
    Quality.objects.filter(id=id).delete()
    messages.success(request,"Quality deleted")
    return redirect('/addquality')

def renderEditQuality(request,id):
    quality=get_object_or_404(Quality,id=id)
    return render(request,'editquality.html',{'id':id,'name':quality.qualities})

def editQuality(request,id):
    quality=get_object_or_404(Quality,id=id)
    p=request.POST.get("edit-quality")
    p = p.upper()
    p = p.strip()
    quality.qualities = p
    quality.save()
    messages.success(request,"Grey Quality edited")
    return redirect('/addquality')

def renderAddLocation(request):
    location_all = ArrivalLocation.objects.all().order_by('location')
    #return render(request,'addparty.html',{'parties':parties_all})

    paginator = Paginator(location_all,10)
    page = request.GET.get('page')
    locations = paginator.get_page(page)
    return render(request,'addlocation.html',{'records':locations})

def saveLocation(request):
    p = request.POST.get("location")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(ArrivalLocation,location=p)
        messages.error(request,"This arrival location already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addarrivallocation')
        new_loc = ArrivalLocation(
            location= p
        )
        new_loc.save()
        messages.success(request,"Arrival location added successfully")
    return redirect('/addarrivallocation')

def deleteLocation(request,id):
    ArrivalLocation.objects.filter(id=id).delete()
    messages.success(request,"Arrival location deleted")
    return redirect('/addarrivallocation')

def renderEditLocation(request,id):
    loc=get_object_or_404(ArrivalLocation,id=id)
    return render(request,'editlocation.html',{'id':id,'name':loc.location})

def editArrivalLocation(request,id):
    party=get_object_or_404(ArrivalLocation,id=id)
    p=request.POST.get("edit-location")
    p = p.upper()
    p = p.strip()
    party.location = p
    party.save()
    messages.success(request,"Arrival location edited")
    return redirect('/addarrivallocation')


#Processing party.......
def renderAddParty(request):
    parties_all = ProcessingPartyName.objects.all().order_by('processing_party')
    #return render(request,'addparty.html',{'parties':parties_all})

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'addparty.html',{'records':parties})

def saveParty(request):
    p = request.POST.get("processing-party")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(ProcessingPartyName,processing_party=p)
        messages.error(request,"This Processing Party already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addparty')
        new_Party = ProcessingPartyName(
            processing_party= p
        )
        new_Party.save()
        messages.success(request,"Processing Party added successfully")
    return redirect('/addparty')

def deleteProcessingParty(request,id):
    ProcessingPartyName.objects.filter(id=id).delete()
    messages.success(request,"Processing House Party deleted")
    return redirect('/addparty')

def renderEditParty(request,id):
    party=get_object_or_404(ProcessingPartyName,id=id)
    return render(request,'editparty.html',{'id':id,'name':party.processing_party})

def editProcessingParty(request,id):
    party=get_object_or_404(ProcessingPartyName,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.processing_party = p
    party.save()
    messages.success(request,"Processing House Party edited")
    return redirect('/addparty')

#processing-----
def showProcessing(request):
    records_list=Record.objects.filter(state="In Process").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
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

    return render(request, 'processing.html',{'records':records,'filter':records_filter,'sums':sums})

def showProcessingRequest(request):
    records_list=Record.objects.filter(state="Checked").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'processingrequest.html',{'records':records,'filter':records_filter})

def processingApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    mindate=str(rec.checking_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    processing_parties = ProcessingPartyName.objects.all().order_by('processing_party')
    d=datetime.date.today()
    d=str(d)
    return render(request, 'processingapprove.html', {'date':d,'record':rec,'parties':processing_parties,'mindate':mindate,'maxdate':maxdate})

def sendInProcess(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_to_process")
    than_recieved = int(than_recieved)
    process_type = request.POST.get("processing-type")
    
    total_amount=prevRec.bill_amount
    totalthan=prevRec.than
    cost_per_than=total_amount/totalthan
    cost_per_than=round(cost_per_than,2)
    if(prevRec.than == than_recieved):
        prevRec.state="In Process"
        prevRec.processing_party_name=request.POST.get("processing-party")
        prevRec.sent_to_processing_date=str(request.POST["sending_date"])
        prevRec.processing_type = process_type
        prevRec.gate_pass = int(request.POST.get('gatepass'))
        prevRec.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/processingrequest')
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
            processing_party_name = request.POST.get("processing-party"),
            processing_type = process_type,
            checking_date = prevRec.checking_date,
            sent_to_processing_date=str(request.POST["sending_date"]),
            total_thans=prevRec.total_thans,
            total_mtrs=prevRec.total_mtrs,
            gate_pass = int(request.POST.get('gatepass'))
            
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
        return redirect('/processingrequest')


#ready to print-----
def showReadyToPrint(request):
    records_list=Record.objects.filter(state="Ready to print").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
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

    return render(request, 'readytoprint.html',{'records':records,'filter':records_filter,'sums':sums})

def showReadyRequest(request):
    records_list=Record.objects.filter(state="In Process").order_by('lot_no')
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'readytoprintrequest.html',{'records':records,'filter':records_filter})

def readyApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    mindate=str(rec.sent_to_processing_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    locations = ArrivalLocation.objects.all().order_by('location')
    d=datetime.date.today()
    d=str(d)
    return render(request, 'readyapprove.html', {'date':d,'record':rec,'mindate':mindate,'maxdate':maxdate,'parties':locations})

def readyToPrint(request,id):
    prevRec = get_object_or_404(Record,id=id)
    location = request.POST.get("arrival-location")
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
        return redirect('/readytoprintrequest')
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
            chalan_no = int(request.POST.get('chalan'))
            
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
        return redirect('/readytoprintrequest')

def reportFilter(request):
    processing_parties = ProcessingPartyName.objects.all().order_by('processing_party')
    partyname =[]
    records = Record.objects.all().order_by('party_name')
    for rec in records:
        if(rec.party_name in partyname):
            pass
        else:
            partyname.append(rec.party_name)
    return render(request,'reportfilter.html',{'parties':processing_parties,'sendingparty':partyname})

def generateReport(request):
    selected_states=['In Process','Ready to print']
    selected_states_all=['Transit','Godown','Checked','In Process','Ready to print']
    selected_parties=[]
    partyname=[]
    send_parties=[]

    send_data=[]

    parties= ProcessingPartyName.objects.all()
    # qualities= Quality.objects.all()
    lot=request.POST.get("lot_no")
    # start_date=request.POST.get("start_date")
    # start_date=datetime.datetime.strptime(str(start_date), '%Y-%m-%d').strftime('%b %d,%Y')
    # end_date=request.POST.get("end_date")
    # end_date=datetime.datetime.strptime(str(end_date), '%Y-%m-%d').strftime('%b %d,%Y')
# jjjj
##  Date filter  
    
    records = Record.objects.all()
    for rec in records:
        if(rec.party_name in partyname):
            pass
        else:
            partyname.append(rec.party_name)

    for p in partyname:
        if(request.POST.get(p)!=None):
            send_parties.append(request.POST.get(p))
    for p in parties:
        if(request.POST.get(p.processing_party)!=None):
            selected_parties.append(request.POST.get(p.processing_party))
    
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
    # print(selected_dates)
# hhhhh date filter end
    
    # for i in range(2):
    #     name="state"+ str(i)
    #     if(request.POST.get(name)!=None):
    #         selected_states.append(request.POST.get(name))

    # for q in qualities:
    #     if(request.POST.get(q.qualities)!=None):
    #         selected_qualities.append(request.POST.get(q.qualities))
    
        if(lot==''):
            if(selected_parties!=[] and send_parties!=[]):
                rec = Record.objects.filter(processing_party_name__in=selected_parties,party_name__in=send_parties,sent_to_processing_date__in=selected_dates)
                
            elif(selected_parties!=[] and send_parties==[]):
                rec = Record.objects.filter(processing_party_name__in=selected_parties,sent_to_processing_date__in=selected_dates)
            elif(selected_parties==[] and send_parties!=[]):
                
                
                for s in send_parties:
                    transit_than=0
                    godown_than=0
                    checked_than=0
                    processing_than=0
                    ready_than=0
                    transit_mtrs=0
                    godown_mtrs=0
                    checked_mtrs=0
                    processing_mtrs=0
                    ready_mtrs=0
                    send_list=[]
                    rec = Record.objects.filter(party_name=s)
                    for r in rec:
                        if(r.state=='Transit'):
                            transit_mtrs=transit_mtrs+r.mtrs
                            transit_than=transit_than+r.than
                        elif(r.state=='Godown'):
                            godown_mtrs=godown_mtrs+r.mtrs
                            godown_than=godown_than+r.than
                        elif(r.state=='In Process'):
                            processing_mtrs=processing_mtrs+r.mtrs
                            processing_than=processing_than+r.than
                        elif(r.state=='Ready to print'):
                            ready_mtrs=ready_mtrs+r.mtrs
                            ready_than=ready_than+r.than
                        else:
                            checked_mtrs=checked_mtrs+r.mtrs
                            checked_than=checked_than+r.than
                    total_than = transit_than + godown_than + checked_than + processing_than + ready_than
                    total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
                    send_list=[s,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
                    send_data.append(send_list)
                return render(request,'reportparty.html',{'data':send_data})
            else:
                rec= Record.objects.filter(sent_to_processing_date__in=selected_dates,state__in=selected_states)            
            
        else:
        
            if(selected_parties!=[] and send_parties!=[]):
                rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties,sent_to_processing_date__in=selected_dates,party_name__in=send_parties) #bill_date__range=[start_date,end_date]
            elif(selected_parties!=[] and send_parties==[]):
                rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties,sent_to_processing_date__in=selected_dates)
            elif(selected_parties==[] and send_parties!=[]):
                
                
                for s in send_parties:
                    transit_than=0
                    godown_than=0
                    checked_than=0
                    processing_than=0
                    ready_than=0
                    transit_mtrs=0
                    godown_mtrs=0
                    checked_mtrs=0
                    processing_mtrs=0
                    ready_mtrs=0
                    send_list=[]
                    rec = Record.objects.filter(lot_no=lot,party_name=s)
                    for r in rec:
                        if(r.state=='Transit'):
                            transit_mtrs=transit_mtrs+r.mtrs
                            transit_than=transit_than+r.than
                        elif(r.state=='Godown'):
                            godown_mtrs=godown_mtrs+r.mtrs
                            godown_than=godown_than+r.than
                        elif(r.state=='In Process'):
                            processing_mtrs=processing_mtrs+r.mtrs
                            processing_than=processing_than+r.than
                        elif(r.state=='Ready to print'):
                            ready_mtrs=ready_mtrs+r.mtrs
                            ready_than=ready_than+r.than
                        else:
                            checked_mtrs=checked_mtrs+r.mtrs
                            checked_than=checked_than+r.than
                    total_than = transit_than + godown_than + checked_than + processing_than + ready_than
                    total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
                    send_list=[s,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
                    send_data.append(send_list)
                return render(request,'reportparty.html',{'data':send_data})
            else:
                rec= Record.objects.filter(lot_no=lot,sent_to_processing_date__in=selected_dates,state__in=selected_states)
                if(len(rec) == 0):
                    rec = Record.objects.filter(lot_no=lot)
                    transit_than=0
                    godown_than=0
                    checked_than=0
                    processing_than=0
                    ready_than=0
                    transit_mtrs=0
                    godown_mtrs=0
                    checked_mtrs=0
                    processing_mtrs=0
                    ready_mtrs=0
                    send_list=[]
                    for r in rec:
                        if(r.state=='Transit'):
                            transit_mtrs=transit_mtrs+r.mtrs
                            transit_than=transit_than+r.than
                        elif(r.state=='Godown'):
                            godown_mtrs=godown_mtrs+r.mtrs
                            godown_than=godown_than+r.than
                        elif(r.state=='In Process'):
                            processing_mtrs=processing_mtrs+r.mtrs
                            processing_than=processing_than+r.than
                        elif(r.state=='Ready to print'):
                            ready_mtrs=ready_mtrs+r.mtrs
                            ready_than=ready_than+r.than
                        else:
                            checked_mtrs=checked_mtrs+r.mtrs
                            checked_than=checked_than+r.than
                    total_than = transit_than + godown_than + checked_than + processing_than + ready_than
                    total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
                    send_list=[lot,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
                    send_data = [send_list]
                    return render(request, 'reportlot.html',{'data':send_data})

        
        return render(request,'report.html',{'records':rec})

    else:
        if(lot==''):
            if(selected_parties!=[] and send_parties!=[]):
                rec = Record.objects.filter(processing_party_name__in=selected_parties,party_name__in=send_parties)
                return render(request,'reportall.html',{'records':rec})
            elif(selected_parties!=[] and send_parties==[]):
                rec = Record.objects.filter(processing_party_name__in=selected_parties)
            elif(selected_parties==[] and send_parties!=[]):
                
                
                for s in send_parties:
                    transit_than=0
                    godown_than=0
                    checked_than=0
                    processing_than=0
                    ready_than=0
                    transit_mtrs=0
                    godown_mtrs=0
                    checked_mtrs=0
                    processing_mtrs=0
                    ready_mtrs=0
                    send_list=[]
                    rec = Record.objects.filter(party_name=s)
                    for r in rec:
                        if(r.state=='Transit'):
                            transit_mtrs=transit_mtrs+r.mtrs
                            transit_than=transit_than+r.than
                        elif(r.state=='Godown'):
                            godown_mtrs=godown_mtrs+r.mtrs
                            godown_than=godown_than+r.than
                        elif(r.state=='In Process'):
                            processing_mtrs=processing_mtrs+r.mtrs
                            processing_than=processing_than+r.than
                        elif(r.state=='Ready to print'):
                            ready_mtrs=ready_mtrs+r.mtrs
                            ready_than=ready_than+r.than
                        else:
                            checked_mtrs=checked_mtrs+r.mtrs
                            checked_than=checked_than+r.than
                    total_than = transit_than + godown_than + checked_than + processing_than + ready_than
                    total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
                    send_list=[s,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
                    send_data.append(send_list)
                return render(request,'reportparty.html',{'data':send_data})
            else:
                rec= Record.objects.filter(state__in=selected_states)            
            
        else:
        
            if(selected_parties!=[] and send_parties!=[]):
                rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties,party_name__in=send_parties) #bill_date__range=[start_date,end_date]
            elif(selected_parties!=[] and send_parties==[]):
                rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties)
            elif(selected_parties==[] and send_parties!=[]):
                
                
                for s in send_parties:
                    transit_than=0
                    godown_than=0
                    checked_than=0
                    processing_than=0
                    ready_than=0
                    transit_mtrs=0
                    godown_mtrs=0
                    checked_mtrs=0
                    processing_mtrs=0
                    ready_mtrs=0
                    send_list=[]
                    rec = Record.objects.filter(lot_no=lot,party_name=s)
                    for r in rec:
                        if(r.state=='Transit'):
                            transit_mtrs=transit_mtrs+r.mtrs
                            transit_than=transit_than+r.than
                        elif(r.state=='Godown'):
                            godown_mtrs=godown_mtrs+r.mtrs
                            godown_than=godown_than+r.than
                        elif(r.state=='In Process'):
                            processing_mtrs=processing_mtrs+r.mtrs
                            processing_than=processing_than+r.than
                        elif(r.state=='Ready to print'):
                            ready_mtrs=ready_mtrs+r.mtrs
                            ready_than=ready_than+r.than
                        else:
                            checked_mtrs=checked_mtrs+r.mtrs
                            checked_than=checked_than+r.than
                    total_than = transit_than + godown_than + checked_than + processing_than + ready_than
                    total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
                    send_list=[s,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
                    send_data.append(send_list)
                return render(request,'reportparty.html',{'data':send_data})
            else:
                rec= Record.objects.filter(lot_no=lot,state__in=selected_states)
                if(len(rec) == 0):
                    rec = Record.objects.filter(lot_no=lot)
                    transit_than=0
                    godown_than=0
                    checked_than=0
                    processing_than=0
                    ready_than=0
                    transit_mtrs=0
                    godown_mtrs=0
                    checked_mtrs=0
                    processing_mtrs=0
                    ready_mtrs=0
                    send_list=[]
                    for r in rec:
                        if(r.state=='Transit'):
                            transit_mtrs=transit_mtrs+r.mtrs
                            transit_than=transit_than+r.than
                        elif(r.state=='Godown'):
                            godown_mtrs=godown_mtrs+r.mtrs
                            godown_than=godown_than+r.than
                        elif(r.state=='In Process'):
                            processing_mtrs=processing_mtrs+r.mtrs
                            processing_than=processing_than+r.than
                        elif(r.state=='Ready to print'):
                            ready_mtrs=ready_mtrs+r.mtrs
                            ready_than=ready_than+r.than
                        else:
                            checked_mtrs=checked_mtrs+r.mtrs
                            checked_than=checked_than+r.than
                    total_than = transit_than + godown_than + checked_than + processing_than + ready_than
                    total_mtrs = transit_mtrs + godown_mtrs + checked_mtrs + processing_mtrs + ready_mtrs
                    send_list=[lot,round(transit_than, 2),round(transit_mtrs, 2),round(godown_than, 2),round(godown_mtrs, 2),round(checked_than, 2),round(checked_mtrs, 2),round(processing_than, 2),round(processing_mtrs, 2),round(ready_than, 2),round(ready_mtrs, 2), round(total_than, 2), round(total_mtrs, 2)]
                    send_data = [send_list]
                    return render(request, 'reportlot.html',{'data':send_data})
        
        return render(request,'report.html',{'records':rec})




def showDefective(request):
    records_list=Record.objects.filter(state__in=['Defect- Transport defect','Defect- Manufacturing defect'])
    records_filter = RecordFilter(request.GET,queryset=records_list)
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    return render(request,'defective.html',{'records':records,'filter':records_filter})


# Ledger
def qualityReportFilter(request):
    qualities= Quality.objects.all().order_by('qualities')
    return render(request,'qualityreportfilter.html',{'qualities':qualities})

def qualityReport(request):
    # qualities=[]
    final_qs=[]
    
    qualities= Quality.objects.all()
    selected_qualities=[]
    for q in qualities:
        
        if(request.POST.get(q.qualities)!=None):
            selected_qualities.append(request.POST.get(q.qualities))
            rec_transit=Record.objects.filter(state="Transit",quality=request.POST.get(q.qualities))
            tally_than=0
            tally_mtrs=0
            total_than_in_transit=0
            total_mtrs_in_transit=0
            
            for r in rec_transit:
                total_than_in_transit=total_than_in_transit+r.than
                total_mtrs_in_transit=total_mtrs_in_transit+r.mtrs

            rec_godown=Record.objects.filter(state="Godown",quality=request.POST.get(q.qualities))
            total_than_in_godown=0
            total_mtrs_in_godown=0
            for r in rec_godown:
                total_than_in_godown=total_than_in_godown+r.than
                total_mtrs_in_godown=total_mtrs_in_godown+r.mtrs
            
            
            rec_checked=Record.objects.filter(state="Checked",quality=request.POST.get(q.qualities))
            total_than_in_checked=0
            total_mtrs_in_checked=0
            for r in rec_checked:
                total_than_in_checked=total_than_in_checked+r.than
                total_mtrs_in_checked=total_mtrs_in_checked+r.mtrs

            rec_process=Record.objects.filter(state="In Process",quality=request.POST.get(q.qualities))
            total_than_in_process=0
            total_mtrs_in_process=0
            for r in rec_process:
                total_than_in_process=total_than_in_process+r.than
                total_mtrs_in_process=total_mtrs_in_process+r.mtrs

            rec_ready=Record.objects.filter(state="Ready to print",quality=request.POST.get(q.qualities))
            total_than_in_ready=0
            total_mtrs_in_ready=0
            for r in rec_ready:
                total_than_in_ready=total_than_in_ready+r.than
                total_mtrs_in_ready=total_mtrs_in_ready+r.mtrs

            tally_mtrs=total_mtrs_in_transit+total_mtrs_in_godown+total_mtrs_in_checked+total_mtrs_in_process+total_mtrs_in_ready
            tally_than=total_than_in_transit+total_than_in_godown+total_than_in_checked+total_than_in_process+total_than_in_ready
            
            d1=[q.qualities,
            total_than_in_transit,round(total_mtrs_in_transit,2),
            total_than_in_godown,round(total_mtrs_in_godown,2),
            total_than_in_checked,round(total_mtrs_in_checked,2),
            total_than_in_process,round(total_mtrs_in_process,2),
            total_than_in_ready,round(total_mtrs_in_ready,2),
            tally_than,round(tally_mtrs,2)
            ]
            
            final_qs.append(d1)
            
            # d=[d1,[1,2,3,4,5],[1,2,3,4,5],[1,2,3,4,5]]
    return render(request,'qualityreport.html',{'data':final_qs})

#Download Excel Files


def export_page_xls(request):
    ur=request.META.get('HTTP_REFERER')
    ur=ur.split('?')
    stateur=ur[0]
    stateur=stateur.split('/')
    stateur=stateur[-1]
    if(stateur=="intransit"):
        file_name="Intransit"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Total Bale', 'Rate', 'LR No', 'Order No', 'State' ]
        records_list=Record.objects.filter(state="Transit").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'state')
    
    elif(stateur=="godown"):
        file_name="Godown"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'State' ]
        records_list=Record.objects.filter(state="Godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    elif(stateur=="checking"):
        file_name="Checked"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'Checking Date', 'State' ]
        records_list=Record.objects.filter(state="Checked").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'rate', 'lr_no', 'order_no', 'recieving_date', 'checking_date', 'state')
    elif(stateur=="inprocess"):
        file_name="InProcess"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Checking Date', 'Sent to Processing Date', 'State', 'Processing Type', 'Processing Party' ]
        records_list=Record.objects.filter(state="In Process").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'rate', 'checking_date', 'sent_to_processing_date', 'state', 'processing_type', 'processing_party_name')
    else:
        file_name="ProcessedGrey"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Sent to Processing Date', 'Processed Date', 'Processing Type', 'Arrival location', 'State' ]
        records_list=Record.objects.filter(state="Ready to print").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'rate', 'sent_to_processing_date', 'recieve_processed_date', 'processing_type', 'arrival_location', 'state')
    

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
    # return render(request,'intransit.html',{'records':records_filter})
    paginator = Paginator(records_filter.qs,20)
    page = d.get('page')
    page=int(page)
    
    records = paginator.get_page(page)
    # rows = Record.objects.filter(state="godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    for row in records:
        row_num += 1
        for col_num in range(len(row)):
            
            ws.write(row_num, col_num, row[col_num], font_style)

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
        records_list=Record.objects.filter(state="Transit").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'state')
    
    elif(stateur=="godown"):
        file_name="Godown-filt"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'State' ]
        records_list=Record.objects.filter(state="Godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    elif(stateur=="checking"):
        file_name="Checked-filt"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'Checking Date', 'State' ]
        records_list=Record.objects.filter(state="Checked").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'rate', 'lr_no', 'order_no', 'recieving_date', 'checking_date', 'state')
    elif(stateur=="inprocess"):
        file_name="InProcess-filt"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Checking Date', 'Sent to Processing Date', 'State', 'Processing Type', 'Processing Party' ]
        records_list=Record.objects.filter(state="In Process").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'rate', 'checking_date', 'sent_to_processing_date', 'state', 'processing_type', 'processing_party_name')
    else:
        file_name="ProcessedGrey-filt"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Sent to Processing Date', 'Processed Date', 'Processing Type', 'Arrival location', 'State' ]
        records_list=Record.objects.filter(state="Ready to print").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'rate', 'sent_to_processing_date', 'recieve_processed_date', 'processing_type', 'arrival_location', 'state')
    


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

    

    records_filter = RecordFilter(d,queryset=records_list)
    
    # rows = Record.objects.filter(state="godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    for row in records_filter.qs:
        row_num += 1
        for col_num in range(len(row)):
            
            ws.write(row_num, col_num, row[col_num], font_style)

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
        records_list=Record.objects.filter(state="Transit").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'total_bale', 'rate', 'lr_no', 'order_no', 'state')
    
    elif(stateur=="godown"):
        file_name="Godown-all"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Bale', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'State' ]
        records_list=Record.objects.filter(state="Godown").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'bale', 'rate', 'lr_no', 'order_no', 'recieving_date', 'state')
    elif(stateur=="checking"):
        file_name="Checked-all"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'LR No', 'Order No', 'Recieving Date', 'Checking Date', 'State' ]
        records_list=Record.objects.filter(state="Checked").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'rate', 'lr_no', 'order_no', 'recieving_date', 'checking_date', 'state')
    elif(stateur=="inprocess"):
        file_name="InProcess-all"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Checking Date', 'Sent to Processing Date', 'State', 'Processing Type', 'Processing Party' ]
        records_list=Record.objects.filter(state="In Process").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'rate', 'checking_date', 'sent_to_processing_date', 'state', 'processing_type', 'processing_party_name')
    else:
        file_name="ProcessedGrey-all"
        columns = ['Party Name', 'Bill No', 'Bill Date', 'Bill Amount', 'Lot No', 'Quality', 'Than', 'Mtrs', 'Rate', 'Sent to Processing Date', 'Processed Date', 'Processing Type', 'Arrival location', 'State' ]
        records_list=Record.objects.filter(state="Ready to print").values_list('party_name', 'bill_no', 'bill_date', 'bill_amount', 'lot_no', 'quality', 'than', 'mtrs', 'rate', 'sent_to_processing_date', 'recieve_processed_date', 'processing_type', 'arrival_location', 'state')
    
    
    
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
            
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    
    return response




###########################################     COLOR    #################################################
def renderAddColorSupplier(request):
    suppliers=ColorSupplier.objects.all().order_by('supplier')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./color/colorsupplier.html',{'suppliers':parties})

def colorhome(request):
    return render(request, './color/colorhome.html')

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
        existing_party=get_object_or_404(ColorSupplier,supplier=p,city=c,address=a)
        messages.error(request,"This Supplier Party already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addcolorsupplier')
        new_Party = ColorSupplier(
            supplier = p,
            address=a,
            city=c
        )
        new_Party.save()
        messages.success(request,"Supplier Party added successfully")
    return redirect('/addcolorsupplier')

def deleteSupplier(request,id):
    ColorSupplier.objects.filter(id=id).delete()
    messages.success(request,"Supplier Party deleted")
    return redirect('/addcolorsupplier')

def renderEditSupplier(request,id):
    party=get_object_or_404(ColorSupplier,id=id)
    return render(request,'./color/editsupplier.html',{'id':id,'name':party.supplier})

def editSupplier(request,id):
    party=get_object_or_404(ColorSupplier,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.supplier = p
    party.save()
    messages.success(request,"Supplier Party edited")
    return redirect('/addcolorsupplier')


##Colormaster
def renderAddColor(request):
    suppliers=Color.objects.all().order_by('color')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./color/addcolor.html',{'suppliers':parties})



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
    Color.objects.filter(id=id).delete()
    messages.success(request,"Color deleted")
    return redirect('/addcolor')

def renderEditColor(request,id):
    party=get_object_or_404(Color,id=id)
    return render(request,'./color/editcolor.html',{'id':id,'name':party.color})

def editColor(request,id):
    party=get_object_or_404(Color,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.color = p
    party.save()
    messages.success(request,"Color edited")
    return redirect('/addcolor')

###########add Godown
def renderAddGodown(request):
    suppliers=Godowns.objects.all().order_by('godown')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./color/addgodown.html',{'suppliers':parties})



def saveGodown(request):
    p = request.POST.get("godown")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(Godowns,godown=p)
        messages.error(request,"This Godown already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addgodown')
        new_Party = Godowns(
            godown = p
        )
        new_Party.save()
        messages.success(request,"Godown added successfully")
    return redirect('/addgodown')

def deleteGodown(request,id):
    Godowns.objects.filter(id=id).delete()
    messages.success(request,"Godown deleted")
    return redirect('/addgodown')

def renderEditGodown(request,id):
    party=get_object_or_404(Godowns,id=id)
    return render(request,'./color/editgodown.html',{'id':id,'name':party.godown})

def editGodown(request,id):
    party=get_object_or_404(Godowns,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.godown = p
    party.save()
    messages.success(request,"Godown edited")
    return redirect('/addgodown')

#############add loose

def renderAddLease(request):
    suppliers=Lease.objects.all().order_by('lease')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./color/addlease.html',{'suppliers':parties})



def saveLease(request):
    p = request.POST.get("lease")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(Lease,lease=p)
        messages.error(request,"This Loose already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addlease')
        new_Party = Lease(
            lease = p
        )
        new_Party.save()
        messages.success(request,"Lease added successfully")
    return redirect('/addlease')

def deleteLease(request,id):
    Lease.objects.filter(id=id).delete()
    messages.success(request,"Lease deleted")
    return redirect('/addlease')

def renderEditLease(request,id):
    party=get_object_or_404(Lease,id=id)
    return render(request,'./color/editlease.html',{'id':id,'name':party.lease})

def editLease(request,id):
    party=get_object_or_404(Lease,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.lease = p
    party.save()
    messages.success(request,"Loose edited")
    return redirect('/addlease')


#######unit master
def renderAddUnit(request):
    suppliers=Units.objects.all().order_by('unit')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./color/addunit.html',{'suppliers':parties})



def saveUnit(request):
    p = request.POST.get("unit")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(Units,unit=p)
        messages.error(request,"This Unit already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addunit')
        new_Party = Units(
            unit = p
        )
        new_Party.save()
        messages.success(request,"Unit added successfully")
    return redirect('/addunit')

def deleteUnit(request,id):
    Units.objects.filter(id=id).delete()
    messages.success(request,"Unit deleted")
    return redirect('/addunit')

def renderEditUnit(request,id):
    party=get_object_or_404(Units,id=id)
    return render(request,'./color/editunit.html',{'id':id,'name':party.unit})

def editUnit(request,id):
    party=get_object_or_404(Units,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.unit = p
    party.save()
    messages.success(request,"Unit edited")
    return redirect('/addunit')

######colorrecord

def placeOrder(request):
    color=Color.objects.all().order_by("color")
    suppliers=ColorSupplier.objects.all().order_by('supplier')
    units=Units.objects.all().order_by('unit')
    
    d=datetime.date.today()
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    d=str(d)
    try:
        rec = ColorRecord.objects.all().order_by('-order_no')[0]
        order_no=rec.order_no + 1
    except:
        order_no = 1
    return render(request,'./color/placeorder.html',{'color':color,'suppliers':suppliers,'units':units,'date':d,'maxdate':maxdate,'orderno':order_no})

def saveOrder(request):
    
    q=int(request.POST.get('quantity'))
    r=float(request.POST.get('rate'))
    a=round(q*r,2)
    new_order=ColorRecord(
        color=request.POST.get('color'),
        supplier=request.POST.get('supplier'),
        order_no=request.POST.get('order_no'),
        order_date=str(request.POST.get('order_date')),
        rate=request.POST.get('rate'),
        amount=a,
        quantity=request.POST.get('quantity'),
        state="Ordered",
        recieving_date=None,
        total_quantity = request.POST.get('quantity'),
        unit = request.POST.get('unit')
    )
    new_order.save()

    new_order=AllOrders(
        color=request.POST.get('color'),
        supplier=request.POST.get('supplier'),
        order_no=request.POST.get('order_no'),
        order_date=str(request.POST.get('order_date')),
        rate=request.POST.get('rate'),
        amount=a,
        quantity=request.POST.get('quantity'),
        state="Ordered",
        unit = request.POST.get('unit'),
        rem_quantity=request.POST.get('quantity')
    )
    new_order.save()
    
    if(request.POST.get('rate2')!='' and request.POST.get('quantity2')!='' and request.POST.get('color2')!=''):
        q=int(request.POST.get('quantity2'))
        r=float(request.POST.get('rate2'))
        a=round(q*r,2)
        new_order=ColorRecord(
            color=request.POST.get('color2'),
            supplier=request.POST.get('supplier'),
            order_no=request.POST.get('order_no'),
            order_date=str(request.POST.get('order_date')),
            rate=request.POST.get('rate2'),
            amount=a,
            quantity=request.POST.get('quantity2'),
            state="Ordered",
            recieving_date=None,
            total_quantity = request.POST.get('quantity2'),
            unit = request.POST.get('unit2')
        )
        new_order.save()

        new_order=AllOrders(
            color=request.POST.get('color2'),
            supplier=request.POST.get('supplier'),
            order_no=request.POST.get('order_no'),
            order_date=str(request.POST.get('order_date')),
            rate=request.POST.get('rate2'),
            amount=a,
            quantity=request.POST.get('quantity2'),
            state="Ordered",
            unit = request.POST.get('unit2'),
            rem_quantity=request.POST.get('quantity2')
        )
        new_order.save()
        if(request.POST.get('rate3')!='' and request.POST.get('quantity3')!='' and request.POST.get('color3')!=''):
            q=int(request.POST.get('quantity3'))
            r=float(request.POST.get('rate3'))
            a=round(q*r,2)
            new_order=ColorRecord(
                color=request.POST.get('color3'),
                supplier=request.POST.get('supplier'),
                order_no=request.POST.get('order_no'),
                order_date=str(request.POST.get('order_date')),
                rate=request.POST.get('rate3'),
                amount=a,
                quantity=request.POST.get('quantity3'),
                state="Ordered",
                recieving_date=None,
                total_quantity = request.POST.get('quantity3'),
                unit = request.POST.get('unit3')
            )
            new_order.save()

            new_order=AllOrders(
                color=request.POST.get('color3'),
                supplier=request.POST.get('supplier'),
                order_no=request.POST.get('order_no'),
                order_date=str(request.POST.get('order_date')),
                rate=request.POST.get('rate3'),
                amount=a,
                quantity=request.POST.get('quantity3'),
                state="Ordered",
                unit = request.POST.get('unit3'),
                rem_quantity=request.POST.get('quantity3')
            )
            new_order.save()

            if(request.POST.get('rate4')!='' and request.POST.get('quantity4')!='' and request.POST.get('color4')!=''):
                q=int(request.POST.get('quantity4'))
                r=float(request.POST.get('rate4'))
                a=round(q*r,2)
                new_order=ColorRecord(
                    color=request.POST.get('color4'),
                    supplier=request.POST.get('supplier'),
                    order_no=request.POST.get('order_no'),
                    order_date=str(request.POST.get('order_date')),
                    rate=request.POST.get('rate4'),
                    amount=a,
                    quantity=request.POST.get('quantity4'),
                    state="Ordered",
                    recieving_date=None,
                    total_quantity = request.POST.get('quantity4'),
                    unit = request.POST.get('unit4')
                )
                new_order.save()

                new_order=AllOrders(
                    color=request.POST.get('color4'),
                    supplier=request.POST.get('supplier'),
                    order_no=request.POST.get('order_no'),
                    order_date=str(request.POST.get('order_date')),
                    rate=request.POST.get('rate4'),
                    amount=a,
                    quantity=request.POST.get('quantity4'),
                    state="Ordered",
                    unit = request.POST.get('unit4'),
                    rem_quantity=request.POST.get('quantity4')
                )
                new_order.save()
    
                if(request.POST.get('rate5')!='' and request.POST.get('quantity5')!='' and request.POST.get('color5')!=''):
                    q=int(request.POST.get('quantity5'))
                    r=float(request.POST.get('rate5'))
                    a=round(q*r,2)
                    new_order=ColorRecord(
                        color=request.POST.get('color5'),
                        supplier=request.POST.get('supplier'),
                        order_no=request.POST.get('order_no'),
                        order_date=str(request.POST.get('order_date')),
                        rate=request.POST.get('rate5'),
                        amount=a,
                        quantity=request.POST.get('quantity5'),
                        state="Ordered",
                        recieving_date=None,
                        total_quantity = request.POST.get('quantity5'),
                        unit = request.POST.get('unit5')
                    )
                    new_order.save()

                    new_order=AllOrders(
                        color=request.POST.get('color5'),
                        supplier=request.POST.get('supplier'),
                        order_no=request.POST.get('order_no'),
                        order_date=str(request.POST.get('order_date')),
                        rate=request.POST.get('rate5'),
                        amount=a,
                        quantity=request.POST.get('quantity5'),
                        state="Ordered",
                        unit = request.POST.get('unit5'),
                        rem_quantity=request.POST.get('quantity5')
                    )
                    new_order.save()

                    if(request.POST.get('rate6')!='' and request.POST.get('quantity6')!='' and request.POST.get('color6')!=''):
                        q=int(request.POST.get('quantity6'))
                        r=float(request.POST.get('rate6'))
                        a=round(q*r,2)
                        new_order=ColorRecord(
                            color=request.POST.get('color6'),
                            supplier=request.POST.get('supplier'),
                            order_no=request.POST.get('order_no'),
                            order_date=str(request.POST.get('order_date')),
                            rate=request.POST.get('rate6'),
                            amount=a,
                            quantity=request.POST.get('quantity6'),
                            state="Ordered",
                            recieving_date=None,
                            total_quantity = request.POST.get('quantity6'),
                            unit = request.POST.get('unit6')
                        )
                        new_order.save()

                        new_order=AllOrders(
                            color=request.POST.get('color6'),
                            supplier=request.POST.get('supplier'),
                            order_no=request.POST.get('order_no'),
                            order_date=str(request.POST.get('order_date')),
                            rate=request.POST.get('rate6'),
                            amount=a,
                            quantity=request.POST.get('quantity6'),
                            state="Ordered",
                            unit = request.POST.get('unit6'),
                            rem_quantity=request.POST.get('quantity6')
                        )
                        new_order.save()

                        if(request.POST.get('rate7')!='' and request.POST.get('quantity7')!='' and request.POST.get('color7')!=''):
                            q=int(request.POST.get('quantity7'))
                            r=float(request.POST.get('rate7'))
                            a=round(q*r,2)
                            new_order=ColorRecord(
                                color=request.POST.get('color7'),
                                supplier=request.POST.get('supplier'),
                                order_no=request.POST.get('order_no'),
                                order_date=str(request.POST.get('order_date')),
                                rate=request.POST.get('rate7'),
                                amount=a,
                                quantity=request.POST.get('quantity7'),
                                state="Ordered",
                                recieving_date=None,
                                total_quantity = request.POST.get('quantity7'),
                                unit = request.POST.get('unit7')
                            )
                            new_order.save()

                            new_order=AllOrders(
                                color=request.POST.get('color7'),
                                supplier=request.POST.get('supplier'),
                                order_no=request.POST.get('order_no'),
                                order_date=str(request.POST.get('order_date')),
                                rate=request.POST.get('rate7'),
                                amount=a,
                                quantity=request.POST.get('quantity7'),
                                state="Ordered",
                                unit = request.POST.get('unit7'),
                                rem_quantity=request.POST.get('quantity7')
                        
                            )
                            new_order.save()

                            if(request.POST.get('rate8')!='' and request.POST.get('quantity8')!='' and request.POST.get('color8')!=''):
                                q=int(request.POST.get('quantity8'))
                                r=float(request.POST.get('rate8'))
                                a=round(q*r,2)
                                new_order=ColorRecord(
                                    color=request.POST.get('color8'),
                                    supplier=request.POST.get('supplier'),
                                    order_no=request.POST.get('order_no'),
                                    order_date=str(request.POST.get('order_date')),
                                    rate=request.POST.get('rate8'),
                                    amount=a,
                                    quantity=request.POST.get('quantity8'),
                                    state="Ordered",
                                    recieving_date=None,
                                    total_quantity = request.POST.get('quantity8'),
                                    unit = request.POST.get('unit8')
                                )
                                new_order.save()

                                new_order=AllOrders(
                                    color=request.POST.get('color8'),
                                    supplier=request.POST.get('supplier'),
                                    order_no=request.POST.get('order_no'),
                                    order_date=str(request.POST.get('order_date')),
                                    rate=request.POST.get('rate8'),
                                    amount=a,
                                    quantity=request.POST.get('quantity8'),
                                    state="Ordered",
                                    unit = request.POST.get('unit8'),
                                    rem_quantity=request.POST.get('quantity8')
                                )
                                new_order.save()

                                if(request.POST.get('rate9')!='' and request.POST.get('quantity9')!='' and request.POST.get('color9')!=''):
                                    q=int(request.POST.get('quantity9'))
                                    r=float(request.POST.get('rate9'))
                                    a=round(q*r,2)
                                    new_order=ColorRecord(
                                        color=request.POST.get('color9'),
                                        supplier=request.POST.get('supplier'),
                                        order_no=request.POST.get('order_no'),
                                        order_date=str(request.POST.get('order_date')),
                                        rate=request.POST.get('rate9'),
                                        amount=a,
                                        quantity=request.POST.get('quantity9'),
                                        state="Ordered",
                                        recieving_date=None,
                                        total_quantity = request.POST.get('quantity9'),
                                        unit = request.POST.get('unit9')
                                    )
                                    new_order.save()

                                    new_order=AllOrders(
                                        color=request.POST.get('color9'),
                                        supplier=request.POST.get('supplier'),
                                        order_no=request.POST.get('order_no'),
                                        order_date=str(request.POST.get('order_date')),
                                        rate=request.POST.get('rate9'),
                                        amount=a,
                                        quantity=request.POST.get('quantity9'),
                                        state="Ordered",
                                        unit = request.POST.get('unit9'),
                                        rem_quantity=request.POST.get('quantity9')
                                    )
                                    new_order.save()

                                    if(request.POST.get('rate10')!='' and request.POST.get('quantity10')!='' and request.POST.get('color10')!=''):
                                        q=int(request.POST.get('quantity10'))
                                        r=float(request.POST.get('rate10'))
                                        a=round(q*r,2)
                                        new_order=ColorRecord(
                                            color=request.POST.get('color10'),
                                            supplier=request.POST.get('supplier'),
                                            order_no=request.POST.get('order_no'),
                                            order_date=str(request.POST.get('order_date')),
                                            rate=request.POST.get('rate10'),
                                            amount=a,
                                            quantity=request.POST.get('quantity10'),
                                            state="Ordered",
                                            recieving_date=None,
                                            total_quantity = request.POST.get('quantity10'),
                                            unit = request.POST.get('unit10')
                                        )
                                        new_order.save()

                                        new_order=AllOrders(
                                            color=request.POST.get('color10'),
                                            supplier=request.POST.get('supplier'),
                                            order_no=request.POST.get('order_no'),
                                            order_date=str(request.POST.get('order_date')),
                                            rate=request.POST.get('rate10'),
                                            amount=a,
                                            quantity=request.POST.get('quantity10'),
                                            state="Ordered",
                                            unit = request.POST.get('unit10'),
                                            rem_quantity=request.POST.get('quantity10')
                                        )
                                        new_order.save()
    messages.success(request,'Order has been Placed')
    return redirect('/placeorder')


def orderGeneration(request):
    rec=AllOrders.objects.all().order_by('order_no')
    records_filter = ColorOrderFilter(request.GET,queryset=rec)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request,'./color/ordergeneration.html',{'records':records,'filter':records_filter})


def orderEdit(request,id):
    rec=get_object_or_404(AllOrders, id=id)
    try:
        #rec2=get_object_or_404(ColorRecord,rate=rec.rate,order_no=rec.order_no,color=rec.color,unit=rec.unit,state="Ordered")
    
        orderdate=str(rec.order_date)
        color = Color.objects.all().order_by('color')
        supplier = ColorSupplier.objects.all().order_by('supplier')
        unit = Units.objects.all().order_by('unit')
        return render(request, './color/editorder.html',{'record':rec,'orderdate':orderdate,'color':color,'suppliers':supplier,'units':unit})
    except:
        messages.error(request,"This order has been recieved")
        return redirect('/ordergeneration')


def orderEditSave(request,id):
    rec_order=get_object_or_404(AllOrders, id=id)
    q=int(request.POST.get('quantity'))
    r=float(request.POST.get('rate'))
    a=q*r
    orderno=rec_order.order_no
    color = rec_order.color
    unit=rec_order.unit
    rate=rec_order.rate
    try:
        rec=get_object_or_404(ColorRecord, rate=rate,order_no=orderno,color=color,unit=unit,state="Ordered")
        rec.supplier=request.POST.get('supplier')
        rec.color=request.POST.get('color')
        rec.order_date=str(request.POST.get('order_date'))                  
        rec.rate=request.POST.get('rate')                               
        rec.amount=a                              
        rec.quantity=request.POST.get('quantity')                   
        rec.total_quantity = request.POST.get('quantity') 
        rec.unit = request.POST.get('unit')         
        rec.save()
    finally:
        rec_order.supplier=request.POST.get('supplier')
        rec_order.color=request.POST.get('color')
        rec_order.order_date=str(request.POST.get('order_date'))                  
        rec_order.rate=request.POST.get('rate')                               
        rec_order.amount=a                              
        rec_order.quantity=request.POST.get('quantity')        
        rec_order.unit = request.POST.get('unit')         
        rec_order.save()
    return redirect('/ordergeneration')


######color in godown

def goodsReceived(request):
    godowns=Godowns.objects.all()
    godowns_list=[]
    for g in godowns:
        godowns_list.append(g.godown)
    godown_colors = GodownLeaseColors.objects.filter(state__in=godowns_list).exclude(quantity=0)
    # rec=ColorRecord.objects.filter(state='Godown').order_by('godown','color')
    records_filter = GodownLeaseFilter(request.GET,queryset=godown_colors)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request,'./color/goodsreceived.html',{'filter':records_filter,'colors':records,'Godown':"Godown Containing"})


    

def goodsRequest(request):
    rec=ColorRecord.objects.filter(state='Ordered').order_by('order_no')
    records_filter = ColorFilter(request.GET,queryset=rec)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request,'./color/goodsrequest.html',{'records':records,'filter':records_filter})

def goods(request,id):
    ogorder=get_object_or_404(AllOrders, id=id)
    rec=get_object_or_404(ColorRecord, order_no=ogorder.order_no,state="Ordered",color = ogorder.color, unit = ogorder.unit)

    mindate=str(rec.order_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    d=datetime.date.today()
    d=str(d)
    orderdate=str(rec.order_date)
    godowns = Godowns.objects.all().order_by('godown')
    return render(request, './color/goodsapprove.html', {'date':d,'record':rec,'mindate':mindate,'maxdate':maxdate,'orderdate':orderdate,'godowns':godowns})

def viewOrder(request,id):
    ogorder = get_object_or_404(AllOrders, id=id)
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
    godowns = Godowns.objects.all().order_by('godown')
    print(billdate)
    remaining_order = 0
    for r in recieved_recs:
        
        remaining_order = remaining_order + r.quantity
    remaining_order = ogorder.quantity - remaining_order
    return render(request, './color/vieworder.html', {'d':d,'billdate':billdate,'record':ogorder,'orderdate':orderdate,'godowns':godowns,'recieved_recs':recieved_recs,'remaining':remaining_order})

def renderValidate(request,id):
    rec=get_object_or_404(AllOrders, id=id)
    mindate=str(rec.order_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    

    return render(request, './color/validateorder.html', {'record':rec,'mindate':mindate,'maxdate':maxdate})

def validate(request,id):
    rec = get_object_or_404(ColorRecord,id=id)
    rec.bill_no=int(request.POST.get('billno'+str(rec.id)))
    rec.bill_date = request.POST.get('billdate'+str(rec.id)) 
    
    rec.save()
    messages.success(request,"Order Validated")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def goodsApprove(request,id):
    prevRec = get_object_or_404(ColorRecord,id=id)
    quantity_recieved = int(request.POST.get("quantityreceived"))
    godown = request.POST.get('godownnumber')
    recieving_date = request.POST.get('receivingdate')
    amount = prevRec.amount
    if(prevRec.quantity == quantity_recieved):
        prevRec.state="Godown"
        prevRec.recieving_date=str(recieving_date)
        prevRec.godown=godown
        prevRec.chalan_no=int(request.POST.get('chalan'))
        prevRec.save()
        ogorder = get_object_or_404(AllOrders,order_no=prevRec.order_no,color=prevRec.color,unit=prevRec.unit)
        ogorder.state="Godown"
        ogorder.rem_quantity = 0
        ogorder.chalan_no=int(request.POST.get('chalan'))
        ogorder.save()
        try:
            godown_color = get_object_or_404(GodownLeaseColors,color=prevRec.color,unit=prevRec.unit,state=godown)
            godown_color.quantity = godown_color.quantity + quantity_recieved
            godown_color.rate = (godown_color.rate + prevRec.rate)/2
            godown_color.save()
            try:
                closing_stock = get_object_or_404(ClosingStock,color=prevRec.color,unit=prevRec.unit,dailydate = datetime.date.today())
                closing_stock.quantity=closing_stock.quantity + quantity_recieved
                closing_stock.save()
            except:
                closing_stock= ClosingStock(
                    color = prevRec.color,
                    quantity = quantity_recieved,
                    unit = prevRec.unit,
                    rate = prevRec.rate,
                    dailydate = datetime.date.today()
                )
                closing_stock.save()
        except:
            godown_color = GodownLeaseColors(
                color = prevRec.color,
                quantity = quantity_recieved,
                unit = prevRec.unit,
                rate = prevRec.rate,
                state = godown
            )
            godown_color.save()
            closing_stock= ClosingStock(
                color = prevRec.color,
                quantity = quantity_recieved,
                unit = prevRec.unit,
                rate = prevRec.rate,
                dailydate = datetime.date.today()
            )
            closing_stock.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/ordergeneration')
    elif(prevRec.quantity<quantity_recieved):
        messages.error(request,"Quantity Recieved cannot be more than Original Amount of Than")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        quantity_remaining = prevRec.quantity - quantity_recieved
        
        amount_per_quant = prevRec.amount/prevRec.quantity
        amount_recieved = amount_per_quant * quantity_recieved
        amount_remain = prevRec.amount - amount_recieved


        value = ColorRecord(
            color=prevRec.color,
            supplier=prevRec.supplier,
            order_no=prevRec.order_no,
            order_date=prevRec.order_date,
            rate=prevRec.rate,
            amount=round(amount_recieved,2),
            quantity=quantity_recieved,
            unit = prevRec.unit,
            state="Godown",
            recieving_date=str(recieving_date),
            total_quantity = prevRec.total_quantity,
            godown = godown,
            chalan_no=int(request.POST.get('chalan'))
            
            )
        if quantity_recieved == 0 :
            messages.error(request,"Quantity Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            value.save()
            prevRec.quantity = prevRec.quantity - quantity_recieved
            prevRec.amount = round(amount_remain,2)
            prevRec.save()
            ogorder = get_object_or_404(AllOrders,order_no=prevRec.order_no,color=prevRec.color,unit=prevRec.unit)
            ogorder.state="In Transit"
            ogorder.rem_quantity= ogorder.rem_quantity - quantity_recieved
            ogorder.save()
            try:
                godown_color = get_object_or_404(GodownLeaseColors,color=prevRec.color,unit=prevRec.unit,state=godown)
                godown_color.quantity = godown_color.quantity + quantity_recieved
                godown_color.rate = (godown_color.rate + prevRec.rate)/2
                godown_color.save()
                try:
                    closing_stock = get_object_or_404(ClosingStock,color=prevRec.color,unit=prevRec.unit,dailydate = datetime.date.today())
                    closing_stock.quantity=closing_stock.quantity + quantity_recieved
                    closing_stock.save()
                except:
                    closing_stock= ClosingStock(
                        color = prevRec.color,
                        quantity = quantity_recieved,
                        unit = prevRec.unit,
                        rate = prevRec.rate,
                        dailydate = datetime.date.today()
                    )
                    closing_stock.save()

            except:
                godown_color = GodownLeaseColors(
                    color = prevRec.color,
                    quantity = quantity_recieved,
                    unit = prevRec.unit,
                    rate = prevRec.rate,
                    state = godown
                )
            godown_color.save()
            closing_stock= ClosingStock(
                color = prevRec.color,
                quantity = quantity_recieved,
                unit = prevRec.unit,
                rate = prevRec.rate,
                dailydate = datetime.date.today()
            )
            closing_stock.save()

            messages.success(request,"Data Updated Successfully")


        #print(than_in_transit,than_in_godown)
        return redirect('/ordergeneration')

    
####lease

def htmltoText(html):
    h=html2text.HTML2Text()
    h.ignore_links=True
    return h.handle(html)


def goodsLease(request):
    lease=Lease.objects.all()
    lease_list=[]
    for g in lease:
        lease_list.append(g.lease)
    godown_colors = GodownLeaseColors.objects.filter(state__in=lease_list).order_by('color')
    # rec=ColorRecord.objects.filter(state='Godown').order_by('godown','color')
    records_filter = GodownLeaseFilter(request.GET,queryset=godown_colors)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    # html = render_to_string('./color/lease.html',{'filter':records_filter,'colors':records})
    # text = htmltoText(html)
    # print(text) 
    return render(request,'./color/lease.html',{'filter':records_filter,'colors':records})

def leaseRequest(request):
    godowns=Godowns.objects.all()
    godowns_list=[]
    for g in godowns:
        godowns_list.append(g.godown)
    godown_colors = GodownLeaseColors.objects.filter(state__in=godowns_list).exclude(quantity=0)
    # rec=ColorRecord.objects.filter(state='Godown').order_by('godown','color')
    records_filter = GodownLeaseFilter(request.GET,queryset=godown_colors)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request,'./color/leaserequest.html',{'filter':records_filter,'colors':records})

def viewGood(request,id):
    rec=get_object_or_404(GodownLeaseColors, id=id)
    # mindate=str(rec.recieving_date)
    # maxdate=datetime.date.today().strftime('%Y-%m-%d')
    d=datetime.date.today()
    d=str(d)
    # recievedate=str(rec.recieving_date)
    lease = Lease.objects.all().order_by('lease')
    return render(request, './color/leaseapprove.html', {'d':d,'record':rec,'lease':lease})


def leaseApprove(request,id):
    prevRec = get_object_or_404(GodownLeaseColors,id=id)
    quantity_recieved = int(request.POST.get("quantitylease"))
    lease = request.POST.get('leasenumber')
    
    if(prevRec.quantity == quantity_recieved):
        
        try:
            godown_color = get_object_or_404(GodownLeaseColors,color=prevRec.color,unit=prevRec.unit,state=lease)
            godown_color.quantity = godown_color.quantity + quantity_recieved
            godown_color.rate = (godown_color.rate + prevRec.rate)/2
            godown_color.save()
        except:
            godown_color = GodownLeaseColors(
                color = prevRec.color,
                quantity = quantity_recieved,
                unit = prevRec.unit,
                rate = prevRec.rate,
                state = lease
            )
            godown_color.save()
        prevRec.quantity=0
        prevRec.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/leaserequest')
    elif(prevRec.quantity<quantity_recieved):
        messages.error(request,"Quantity Recieved cannot be more than Original Amount of Than")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        quantity_remaining = prevRec.quantity - quantity_recieved
        try:
            godown_color = get_object_or_404(GodownLeaseColors,color=prevRec.color,unit=prevRec.unit,state=lease)
            godown_color.quantity = godown_color.quantity + quantity_recieved
            godown_color.rate = (godown_color.rate + prevRec.rate)/2
            
        except:
            godown_color = GodownLeaseColors(
                color = prevRec.color,
                quantity = quantity_recieved,
                unit = prevRec.unit,
                rate = prevRec.rate,
                state = lease
            )

        if quantity_recieved == 0 :
            messages.error(request,"Quantity Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            prevRec.quantity=quantity_remaining
            prevRec.save()
            godown_color.save()
            messages.success(request,"Data Updated Successfully")
            
            
    return redirect('/leaserequest')

    

def renderDailyConsumptionLease1(request):                                                      ####repair required 
    lease = Lease.objects.all().order_by('lease')
    first_lease = Lease.objects.all().order_by('lease').first()
    try:
        color = GodownLeaseColors.objects.filter(state=first_lease.lease).order_by('color')
    except:
        new_value = Lease(lease="Loose Godown 1")
        new_value.save()
        color = GodownLeaseColors.objects.filter(state="Loose Godown 1").order_by('color')
    todays = DailyConsumption.objects.filter(con_date=str(datetime.date.today()))
    
    return render(request,'./color/dailyconsumption.html',{'colors':color,'todays':todays,'lease':lease,'name':first_lease.lease})

def renderDailyConsumptionLease2(request):
    lease = request.POST.get('lease')
    leases = Lease.objects.all().order_by('lease')
    color = GodownLeaseColors.objects.filter(state=lease).order_by('color')
    todays = DailyConsumption.objects.filter(con_date=str(datetime.date.today()))
    
    return render(request,'./color/dailyconsumption.html',{'colors':color,'todays':todays,'lease':leases,'name':lease})



def consume(request,name):
    colors = GodownLeaseColors.objects.filter(state=name).exclude(quantity=0).order_by('color')
    flag = 0
    for c in colors:
        if(int(request.POST.get(str(c.id)))>c.quantity):
            flag = flag + 1
            continue
        try:
            closing_stock = ClosingStock.objects.filter(color=c.color,unit=c.unit).order_by('-dailydate').first()
            if(closing_stock.dailydate != datetime.date.today()):
                new_cs = ClosingStock(
                    color=c.color,
                    unit=c.unit,
                    quantity=closing_stock.quantity - int(request.POST.get(str(c.id))),
                    dailydate=datetime.date.today(),
                    rate=c.rate
                )
                new_cs.save()
            else:
                closing_stock.quantity=closing_stock.quantity - int(request.POST.get(str(c.id)))
                closing_stock.save()
        except:
            pass
        c.quantity=c.quantity - int(request.POST.get(str(c.id)))
        c.save()
        stored_color = GodownLeaseColors.objects.filter(color=c.color,unit=c.unit)
        q=0
        for sc in stored_color:
            q=q+sc.quantity

        daily_consump = DailyConsumption(
            con_date = datetime.date.today(),
            color = c.color,
            unit = c.unit,
            quantity = int(request.POST.get(str(c.id))),
            quantity_remaining = q
        )
        daily_consump.save()
   
    if (flag != 0):
        messages.error(request,"%s Quantity entered exceeded the quantities available in Loose" %(flag))
    return redirect('/dailyconsumption1')



def renderClosingStock(request):
    godowns=Godowns.objects.all()
    godowns_list=[]
    for g in godowns:
        godowns_list.append(g.godown)

    lease=Lease.objects.all()
    lease_list=[]
    for l in lease:
        lease_list.append(l.lease)

    datalist=[]
    colors=Color.objects.all()
    units=Units.objects.all()
    for c in colors:
        for u in units:
            try:
                lq=0
                recsl=get_list_or_404(GodownLeaseColors,color=c.color,unit=u.unit,state__in=lease_list)
                for i in recsl:
                    lq=lq+i.quantity
                
                recsg=get_list_or_404(GodownLeaseColors,color=c.color,unit=u.unit,state__in=godowns_list)
                lg=0
                for i in recsg:
                    lg=lg+i.quantity
                l=[]
                l.append(c.color)
                l.append(u.unit)
                l.append(lq)
                l.append(lg)
                l.append(lq+lg)
                datalist.append(l)
            except:
                try:
                    recsg=get_list_or_404(GodownLeaseColors,color=c.color,unit=u.unit,state__in=godowns_list)
   
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
    

    return render(request,'./color/closingstock.html',{'colors':datalist})

def renderColorReportFilter(request):
    return render(request,'./color/reportfilter.html')

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
        
#     return render(request,'./color/report.html',{'data':datalist,'begin':begin,'end':end})


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
    units= Units.objects.all()
    for c in colors:
        for u in units:
            try:
                l=[]
                try:
                    first_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[0],color = c.color,unit = u.unit).order_by('-dailydate').first()
                    l.append(c.color)
                    l.append(u.unit)
                    l.append(first_record.quantity)
                except:

                    l.append(0)
                try:
                    last_record = get_object_or_404(ClosingStock,dailydate=selected_dates[-1],color = c.color,unit = u.unit)
                except:
                    last_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[-1],color = c.color,unit = u.unit).order_by('-dailydate').first()
                
                
                try:
                    records=get_list_or_404(DailyConsumption,con_date__in=selected_dates,color=c.color,unit=u.unit)
                    
                    
                    quantity = 0
                    for rec in records:
                        quantity = quantity+rec.quantity
                
                    l.append(quantity)
                except:
                    l.append(0)
                
                l.append(last_record.quantity)
                # new_stock=(l[4]-l[3])
                # if(new_stock>0):
                #     l.append(new_stock)
                new_stock=0
                try:
                    neworders = get_list_or_404(ColorRecord,recieving_date__in=selected_dates,color=c.color,unit=u.unit)
                    for i in neworders:
                        new_stock=new_stock+i.quantity
                except:
                    pass

                l.append(new_stock)
                datalist.append(l)
                print(first_record.quantity,first_record.con_date)
            except:
                print("ee")
        
    return render(request,'./color/report.html',{'data':datalist,'begin':begin,'end':end})


##################################### Module 3 - Employee ######################################
def employeehome(request):
    return render(request, './employee/employeehome.html')
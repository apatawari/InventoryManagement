from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.template import RequestContext
from .models import Record,Quality
from .resources import ItemResources
from .filters import RecordFilter
from django.contrib import messages
from tablib import Dataset
from django.contrib import messages
from django.http import HttpResponseRedirect
import pandas
import numpy as np


# Create your views here.
def index(request):
    return render(request, 'index.html')



def upload(request):
    counter = 0
    if request.method == 'POST':
        item_resource = ItemResources()
        dataset = Dataset()
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
        for data in imported_data:
            try:
                rec=get_object_or_404(Record, 
                    party_name=data[1],
                    bill_no=data[2],
                    bill_date=data[3],
                    bill_amount=data[4],
                    lot_no=data[5],
                    quality=data[6],
                    than=data[7],
                    mtrs=data[8],
                    bale=data[9],
                    rate=data[10],
                    lr_no=data[11],
                    order_no=data[12])
            except:
                
                value = Record(
                    sr_no=data[0],
                    party_name=data[1],
                    bill_no=data[2],
                    bill_date=data[3],
                    bill_amount=data[4],
                    lot_no=data[5],
                    quality=data[6],
                    than=data[7],
                    mtrs=data[8],
                    bale=data[9],
                    rate=data[10],
                    lr_no=data[11],
                    order_no=data[12]
                    )
                value.save()
                counter = counter + 1
                try:
                    rec=get_object_or_404(Quality,
                        qualities=data[6])
                except:
                    new_quality = Quality(
                        qualities=data[6]
                        )
                    new_quality.save()

        if (counter > 0):
            messages.success(request,str(counter)+ " Records were Inserted")
        else:
            messages.error(request, "No Records were Inserted")


    return render(request, 'index.html')

def showIntransit(request):
    records_list=Record.objects.filter(state="Transit")
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'intransit.html',{'records':records,'filter':records_filter})
    

def showGodown(request):
    records_list=Record.objects.filter(state="Godown")
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'godown.html',{'records':records,'filter':records_filter})

def showGodownRequest(request):
    records_list=Record.objects.filter(state="Transit")
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
    qualities = Quality.objects.all()
    return render(request, 'godownapprove.html', {'record':rec,'qualities':qualities})

def edit(request,id):
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
    if(prevRec.bale == bale_recieved):
        prevRec.state="Godown"
        prevRec.recieving_date=str(request.POST["recieving_date"])
        prevRec.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/godown')
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
            bill_amount=prevRec.bill_amount,
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
            
            )

        if bale_recieved == 0 :
            messages.error(request,"Bale Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            value.save()
            prevRec.bale = bale_in_transit
            prevRec.than = than_in_transit
            prevRec.mtrs = mtrs_in_transit
            prevRec.save()
            messages.success(request,"Data Updated Successfully")
        #print(than_in_transit,than_in_godown)
        return redirect('/godown')

#quality2 = request.POST.get("quality2")

def showChecked(request):
    records_list=Record.objects.filter(state="Checked")
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'checking.html',{'records':records,'filter':records_filter})

def showCheckingRequest(request):
    records_list=Record.objects.filter(state="Godown")
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'checkingrequest.html',{'records':records,'filter':records_filter})

def checkingApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    qualities_all = Quality.objects.all().order_by('qualities')
    return render(request, 'checkingapprove.html', {'record':rec,'qualities':qualities_all})

def approveCheck(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_recieved")
    than_recieved = int(than_recieved)
    if(prevRec.than == than_recieved):
        prevRec.state="Checked"
        prevRec.quality=request.POST.get("new-quality")
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
            bill_amount=prevRec.bill_amount,
            lot_no=prevRec.lot_no,
            quality=request.POST.get("new-quality"),
            than=than_recieved,
            mtrs=mtrs_checked,
            bale=bale_checked,
            rate=prevRec.rate,
            lr_no=prevRec.lr_no,
            order_no=prevRec.order_no,
            state="Checked",
            recieving_date =prevRec.recieving_date
            
            )
        if than_recieved == 0 :
            messages.error(request,"Than Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            value.save()
            prevRec.bale = bale_un_checked
            prevRec.than = than_un_checked
            prevRec.mtrs = mtrs_un_checked
            prevRec.save()
            messages.success(request,"Data Updated Successfully")
        #print(than_in_transit,than_in_godown)
        return redirect('/checking')

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
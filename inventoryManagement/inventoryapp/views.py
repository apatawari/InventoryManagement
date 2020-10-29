from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.template import RequestContext
from .models import Record,Quality,ProcessingPartyName
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
                    bill_amount=data[4],
                    lot_no=data[5],
                    lr_no=data[11],
                    order_no=data[12])
            except:
                
                value = Record(
                    sr_no=data[0],
                    party_name=data[1],
                    bill_no=data[2],
                    bill_date=(data[3]).date(),
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
            messages.error(request, "These records already exist")


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
        prevRec.checking_date=str(request.POST["checking_date"])
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

def renderAddParty(request):
    parties_all = ProcessingPartyName.objects.all().order_by('processing_party')
    #return render(request,'addparty.html',{'parties':parties_all})

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'addparty.html',{'records':parties})

def saveParty(request):
    p = request.POST.get("processing-party")
    p=p.upper()
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

#processing-----
def showProcessing(request):
    records_list=Record.objects.filter(state="In Process")
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'processing.html',{'records':records,'filter':records_filter})

def showProcessingRequest(request):
    records_list=Record.objects.filter(state="Checked")
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'processingrequest.html',{'records':records,'filter':records_filter})

def processingApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    processing_parties = ProcessingPartyName.objects.all().order_by('processing_party')
    return render(request, 'processingapprove.html', {'record':rec,'parties':processing_parties})

def sendInProcess(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_to_process")
    than_recieved = int(than_recieved)
    if(prevRec.than == than_recieved):
        prevRec.state="In Process"
        prevRec.processing_party_name=request.POST.get("processing-party")
        prevRec.sent_to_processing_date=str(request.POST["sending_date"]) 
        prevRec.save()
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
            bill_amount=prevRec.bill_amount,
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
            sent_to_processing_date=str(request.POST["sending_date"]),
            total_thans=prevRec.total_thans,
            total_mtrs=prevRec.total_mtrs
            
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
        return redirect('/inprocess')


#ready to print-----
def showReadyToPrint(request):
    records_list=Record.objects.filter(state="Ready to print")
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'readytoprint.html',{'records':records,'filter':records_filter})

def showReadyRequest(request):
    records_list=Record.objects.filter(state="In Process")
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'readytoprintrequest.html',{'records':records,'filter':records_filter})

def readyApprove(request,id):
    rec=get_object_or_404(Record, id=id)
    #processing_parties = ProcessingPartyName.objects.all().order_by('processing_party')
    return render(request, 'readyapprove.html', {'record':rec})

def readyToPrint(request,id):
    prevRec = get_object_or_404(Record,id=id)
    tally_lot_no = prevRec.lot_no
    tally_total_thans=prevRec.total_thans
    than_recieved=request.POST.get("than_ready")
    than_recieved = int(than_recieved)
    if(prevRec.than == than_recieved):
        prevRec.state="Ready to print"
        prevRec.recieve_processed_date=str(request.POST.get("processing_date"))

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
        return redirect('/readytoprint')
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
            recieve_processed_date=str(request.POST.get("processing_date")),
            total_mtrs=prevRec.total_mtrs,
            total_thans=prevRec.total_thans
            
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
        return redirect('/readytoprint')
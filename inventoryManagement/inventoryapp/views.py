from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.template import RequestContext
from .models import Record,Quality,ProcessingPartyName,ArrivalLocation
from .resources import ItemResources
from .filters import RecordFilter
from django.contrib import messages
from tablib import Dataset
from django.http import HttpResponseRedirect
import pandas
import numpy as np
import datetime

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


# Create your views here.
def index(request):
    return render(request, 'index.html')

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
            return redirect('/index')
            
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

        if (counter > 0):
            messages.success(request,str(counter)+ " Records were Inserted")
        else:
            messages.error(request, "These records already exist")


    return redirect('/index')

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
    mindate=datetime.datetime.strptime(rec.bill_date,'%b %d,%Y').strftime('%Y-%m-%d')
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    qualities = Quality.objects.all()
    return render(request, 'godownapprove.html', {'record':rec,'qualities':qualities,'mindate':mindate,'maxdate':maxdate})

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

    mindate=str(rec.recieving_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    qualities_all = Quality.objects.all().order_by('qualities')
    return render(request, 'checkingapprove.html', {'record':rec,'qualities':qualities_all,'mindate':mindate,'maxdate':maxdate})

def approveCheck(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_recieved")
    than_recieved = int(than_recieved)
    defect=request.POST.get("defect")

    if(defect=="no defect"):
    
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
                
    else:
        if(prevRec.than == than_recieved):
            prevRec.state=request.POST.get("defect")
            prevRec.quality=request.POST.get("new-quality")
            prevRec.checking_date=str(request.POST["checking_date"])
            prevRec.save()
            messages.success(request,"Data updated to defective state")

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
                prevRec.save()
                messages.success(request,"Data updated to defective state")

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

def deleteQuality(request,id):
    Quality.objects.filter(id=id).delete()
    messages.success(request,"Quality deleted")
    return redirect('/addquality')

def renderEditQuality(request,id):
    quality=get_object_or_404(Quality,id=id)
    return render(request,'editquality.html',{'id':id,'name':quality.qualities})

def editQuality(request,id):
    quality=get_object_or_404(Quality,id=id)
    quality.qualities = request.POST.get("edit-quality")
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
    p=p.upper()
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
    party.location = request.POST.get("edit-location")
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

def deleteProcessingParty(request,id):
    ProcessingPartyName.objects.filter(id=id).delete()
    messages.success(request,"Processing House Party deleted")
    return redirect('/addparty')

def renderEditParty(request,id):
    party=get_object_or_404(ProcessingPartyName,id=id)
    return render(request,'editparty.html',{'id':id,'name':party.processing_party})

def editProcessingParty(request,id):
    party=get_object_or_404(ProcessingPartyName,id=id)
    party.processing_party = request.POST.get("edit-party")
    party.save()
    messages.success(request,"Processing House Party edited")
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
    mindate=str(rec.checking_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    processing_parties = ProcessingPartyName.objects.all().order_by('processing_party')
    return render(request, 'processingapprove.html', {'record':rec,'parties':processing_parties,'mindate':mindate,'maxdate':maxdate})

def sendInProcess(request,id):
    prevRec = get_object_or_404(Record,id=id)
    than_recieved=request.POST.get("than_to_process")
    than_recieved = int(than_recieved)
    process_type = request.POST.get("processing-type")
    if(prevRec.than == than_recieved):
        prevRec.state="In Process"
        prevRec.processing_party_name=request.POST.get("processing-party")
        prevRec.sent_to_processing_date=str(request.POST["sending_date"])
        prevRec.processing_type = process_type 
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
            processing_type = process_type,
            checking_date = prevRec.checking_date,
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
    mindate=str(rec.sent_to_processing_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    locations = ArrivalLocation.objects.all().order_by('location')
    return render(request, 'readyapprove.html', {'record':rec,'mindate':mindate,'maxdate':maxdate,'parties':locations})

def readyToPrint(request,id):
    prevRec = get_object_or_404(Record,id=id)
    location = request.POST.get("arrival-location")
    tally_lot_no = prevRec.lot_no
    tally_total_thans=prevRec.total_thans
    than_recieved=request.POST.get("than_ready")
    than_recieved = int(than_recieved)
    if(prevRec.than == than_recieved):
        prevRec.state="Ready to print"
        prevRec.recieve_processed_date=str(request.POST.get("processing_date"))
        prevRec.arrival_location = location
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
            sent_to_processing_date = prevRec.sent_to_processing_date,
            recieve_processed_date=str(request.POST.get("processing_date")),
            total_mtrs=prevRec.total_mtrs,
            total_thans=prevRec.total_thans,
            arrival_location=location
            
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

def reportFilter(request):
    processing_parties= ProcessingPartyName.objects.all()
    qualities= Quality.objects.all()


    return render(request,'reportfilter.html',{'parties':processing_parties,'qualities':qualities})

def generateReport2(request):                   #deprecated version
    parties= ProcessingPartyName.objects.all()
    qualities= Quality.objects.all()
    lot=request.POST.get("lot_no")
    # start_date=request.POST.get("start_date")
    # start_date=datetime.datetime.strptime(str(start_date), '%Y-%m-%d').strftime('%b %d,%Y')
    # end_date=request.POST.get("end_date")
    # end_date=datetime.datetime.strptime(str(end_date), '%Y-%m-%d').strftime('%b %d,%Y')
# jjjj
##  Date filter  
    begin = request.POST.get("start_date")
    end = request.POST.get("end_date")
    begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
    end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
    selected_dates=[]
    selected_states=[]
    selected_parties=[]
    selected_qualities=[]
    next_day = begin
    while True:
        if next_day > end:
            break
    
        
    
        selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d').strftime('%b %d,%Y'))
        next_day += datetime.timedelta(days=1)
    # print(selected_dates)
# hhhhh date filter end
    
    for i in range(5):
        name="state"+ str(i)
        if(request.POST.get(name)!=None):
            selected_states.append(request.POST.get(name))

    for q in qualities:
        if(request.POST.get(q.qualities)!=None):
            selected_qualities.append(request.POST.get(q.qualities))
    
    for p in parties:
        if(request.POST.get(p.processing_party)!=None):
            selected_parties.append(request.POST.get(p.processing_party))
    

    if(lot==''):
        if(selected_states==[]):
            if(selected_qualities!=[] and selected_parties!=[]):
                rec = Record.objects.filter(quality__in=selected_qualities,processing_party_name__in=selected_parties,bill_date__in=selected_dates)
            elif(selected_qualities!=[] and selected_parties==[]):
                rec = Record.objects.filter(quality__in=selected_qualities,bill_date__in=selected_dates)
            elif(selected_qualities==[] and selected_parties!=[]):
                rec = Record.objects.filter(processing_party_name__in=selected_parties,bill_date__in=selected_dates)
            else:
                rec= Record.objects.filter(bill_date__in=selected_dates)            
            # rec= Record.objects.filter(bill_date__range=[start_date,end_date])
            # rec = Record.objects.raw('select * from Record where bill_date from "' +start_date+'" and "' +end_date+'"')
        else:
            if(selected_qualities!=[] and selected_parties!=[]):
                rec = Record.objects.filter(quality__in=selected_qualities,processing_party_name__in=selected_parties,bill_date__in=selected_dates,state__in=selected_states)
            elif(selected_qualities!=[] and selected_parties==[]):
                rec = Record.objects.filter(quality__in=selected_qualities,bill_date__in=selected_dates,state__in=selected_states)
            elif(selected_qualities==[] and selected_parties!=[]):
                rec = Record.objects.filter(processing_party_name__in=selected_parties,bill_date__in=selected_dates,state__in=selected_states)
            else:
                rec= Record.objects.filter(bill_date__in=selected_dates,state__in=selected_states)
                print("this")

    else:
        if(selected_states==[]):
            if(selected_qualities!=[] and selected_parties!=[]):
                rec = Record.objects.filter(lot_no=lot,quality__in=selected_qualities,processing_party_name__in=selected_parties,bill_date__in=selected_dates) #bill_date__range=[start_date,end_date]
            elif(selected_qualities!=[] and selected_parties==[]):
                rec = Record.objects.filter(lot_no=lot,quality__in=selected_qualities,bill_date__in=selected_dates)
            elif(selected_qualities==[] and selected_parties!=[]):
                rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties,bill_date__in=selected_dates)
            else:
                rec= Record.objects.filter(lot_no=lot,bill_date__in=selected_dates)
        else:
            if(selected_qualities!=[] and selected_parties!=[]):
                rec = Record.objects.filter(lot_no=lot,quality__in=selected_qualities,processing_party_name__in=selected_parties,bill_date__in=selected_dates,state__in=selected_states) #bill_date__range=[start_date,end_date]
            elif(selected_qualities!=[] and selected_parties==[]):
                rec = Record.objects.filter(lot_no=lot,quality__in=selected_qualities,bill_date__in=selected_dates,state__in=selected_states)
            elif(selected_qualities==[] and selected_parties!=[]):
                rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties,bill_date__in=selected_dates,state__in=selected_states)
            else:
                rec= Record.objects.filter(lot_no=lot,bill_date__in=selected_dates,state__in=selected_states)
    
    return render(request,'report.html',{'records':rec})


def generateReport(request):
    parties= ProcessingPartyName.objects.all()
    # qualities= Quality.objects.all()
    lot=request.POST.get("lot_no")
    # start_date=request.POST.get("start_date")
    # start_date=datetime.datetime.strptime(str(start_date), '%Y-%m-%d').strftime('%b %d,%Y')
    # end_date=request.POST.get("end_date")
    # end_date=datetime.datetime.strptime(str(end_date), '%Y-%m-%d').strftime('%b %d,%Y')
# jjjj
##  Date filter  
    begin = request.POST.get("start_date")
    end = request.POST.get("end_date")
    begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
    end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
    selected_dates=[]
    selected_states=['In Process','Ready to print']
    selected_parties=[]
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
    
    for p in parties:
        if(request.POST.get(p.processing_party)!=None):
            selected_parties.append(request.POST.get(p.processing_party))
    

    if(lot==''):
        if(selected_parties!=[]):
            rec = Record.objects.filter(processing_party_name__in=selected_parties,sent_to_processing_date__in=selected_dates)
        else:
            rec= Record.objects.filter(sent_to_processing_date__in=selected_dates,state__in=selected_states)            
            
    else:
        
        if(selected_parties!=[]):
            rec = Record.objects.filter(lot_no=lot,processing_party_name__in=selected_parties,sent_to_processing_date__in=selected_dates) #bill_date__range=[start_date,end_date]
        else:
            rec= Record.objects.filter(lot_no=lot,sent_to_processing_date__in=selected_dates,state__in=selected_states)
        
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


            d1=[q.qualities,
            total_than_in_transit,round(total_mtrs_in_transit,2),
            total_than_in_godown,round(total_mtrs_in_godown,2),
            total_than_in_checked,round(total_mtrs_in_checked,2),
            total_than_in_process,round(total_mtrs_in_process,2),
            total_than_in_ready,round(total_mtrs_in_ready,2)
            ]
            
            final_qs.append(d1)
            
            # d=[d1,[1,2,3,4,5],[1,2,3,4,5],[1,2,3,4,5]]
    return render(request,'qualityreport.html',{'data':final_qs})
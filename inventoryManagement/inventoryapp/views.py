from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.template import RequestContext
from .models import Record
from .resources import ItemResources
from .filters import RecordFilter
from django.contrib import messages
from tablib import Dataset
import pandas
import numpy as np


# Create your views here.
def index(request):
    return render(request, 'index.html')


# def insert(request):
#     if request.method == 'POST':
#         return HttpResponse(request.FILES['myfile'].name)
#     else:
#         return HttpResponse("nofile")


def upload(request):
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
        
        #result = person_resource.import_data(dataset, dry_run=True)  # Test the data import

        # if not result.has_errors():
        #    item_resource.import_data(dataset, dry_run=False)  # Actually import now

    # return render(request, 'index.html')
    return HttpResponse("done")

def showIntransit(request):
    records_list=Record.objects.all()
    records_filter = RecordFilter(request.GET,queryset=records_list)
    # return render(request,'intransit.html',{'records':records_filter})
    
    paginator = Paginator(records_filter.qs,10)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request, 'intransit.html',{'records':records,'filter':records_filter})
    

    # records = Record.objects.all()
    # paginator = Paginator(records,10)
    # page = request.GET.get('page')
    # records = paginator.get_page(page)

    # return render(request, 'intransit.html',{'records':records})

def record(request,id):
    rec=get_object_or_404(Record, id=id)
    return render(request, 'record.html', {'record':rec})

def edit(request,id):
    if request.method=="POST":
        record = get_object_or_404(Record,id=id)
        record.party_name=request.POST.get("party_name")
        record.bill_no=request.POST.get("bill_no")
        record.bill_amount=request.POST.get("bill_amount")
        record.lot_no=request.POST.get("lot_no")
        record.quality=request.POST.get("quality")
        record.than=request.POST.get("than")
        record.mtrs=request.POST.get("mtrs")
        record.bale=request.POST.get("bale")
        record.rate=request.POST.get("rate")
        record.lr_no=request.POST.get("lr_no")
        record.order_no=request.POST.get("order_no")
        record.save()
        return redirect('/intransit')
        # records=Record.objects.all()
        
        # return render(request,'intransit.html',{'records':records})
        
# def searchIntransit(request):
#     records_list=Record.objects.all()
#     records_filter = RecordFilter(request.GET,queryset=records_list)
#     return render(request,'intransit.html',{'records':records_filter})
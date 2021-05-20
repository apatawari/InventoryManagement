from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,SalesQualityMaster
from inventoryapp.resources import ItemResources
from inventoryapp.filters import RecordFilter
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

############ SALES : QUALITY MASTER ############
def renderSalesMasterQuality(request):

    all_quality = SalesQualityMaster.objects.all().order_by('sales_quality_name')
    paginator = Paginator(all_quality,10)
    page = request.GET.get('page')
    quality_name = paginator.get_page(page)

    return render(request,'./SalesModule/SalesMaster/masterSalesQuality.html',{'records':quality_name})


def saveSalesMasterQuality(request):

    quality_name = request.POST.get("sales_quality_name")
    quality_name = quality_name.strip()
    try:
        existing_quality=get_object_or_404(SalesQualityMaster,quality_name=quality_name.upper())
        messages.error(request,"The sale quality already exists with name: "+quality_name)
    except:
        if quality_name=="":
            messages.error(request,"Please enter valid sale quality name")
            return redirect('/renderMasterQuality')
        new_sale_quality = SalesQualityMaster(
            sales_quality_name=quality_name.upper()
        )
        new_sale_quality.save()
        messages.success(request,"Sales Quality added")
    return redirect('/renderSalesMasterQuality')


def deleteSalesMasterQuality(request,id):

    try:
        SalesQualityMaster.objects.filter(id=id).delete()
        messages.success(request,"Sales Quality Removed")
    except:
        messages.error(request,"Cannot delete this sale quality - it is in use")
    return redirect('/renderSalesMasterQuality')



def renderEditSalesMasterQuality(request,id):

    quality=get_object_or_404(SalesQualityMaster,id=id)
    return render(request,'./SalesModule/SalesMaster/editSalesMasterQuality.html',{'id':id,'name':quality.sales_quality_name})



def editSalesMasterQuality(request,id):

    quality=get_object_or_404(SalesQualityMaster,id=id)
    p = request.POST.get("edit-sale-quality").upper().strip()
    try:
        existing_quality=get_object_or_404(SalesQualityMaster,quality_name=p.upper())
        messages.error(request,"The sale quality already exists")
    except:
        if p.strip()=="":
            messages.error(request,"Please provide the sale quality name as input")
            return redirect('/renderMasterQuality')
        quality.sales_quality_name = p
        quality.save()
        messages.success(request,"Sales Quality Updated")

    return redirect('/renderSalesMasterQuality')

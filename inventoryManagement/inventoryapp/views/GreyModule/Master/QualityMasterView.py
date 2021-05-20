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




############ GREY : QUALITY MASTER ############

def renderGreyMasterQuality(request):
    all_quality = GreyQualityMaster.objects.all().order_by('quality_name')
    #return render(request,'./GreyModule/GreyMaster/addquality.html',{'allquality':all_quality})
    paginator = Paginator(all_quality,10)
    page = request.GET.get('page')
    quality_name = paginator.get_page(page)

    return render(request,'./GreyModule/GreyMaster/masterGreyQuality.html',{'records':quality_name})

def saveGreyMasterQuality(request):
    quality_name = request.POST.get("quality_name")
    quality_name = quality_name.strip()

    quality_name = quality_name.replace('"','inch')
    try:
        existing_quality=get_object_or_404(GreyQualityMaster,quality_name=quality_name.upper())
        messages.error(request,"This quality already exists")
    except:
        if quality_name.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/renderMasterQuality')
        new_quality = GreyQualityMaster(
            quality_name=quality_name.upper()
        )
        new_quality.save()
        messages.success(request,"Grey Quality added")
    return redirect('/renderGreyMasterQuality')

def deleteGreyMasterQuality(request,id):
    try:
        GreyQualityMaster.objects.filter(id=id).delete()
        messages.success(request,"Grey Quality deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/renderGreyMasterQuality')

def renderEditGreyMasterQuality(request,id):
    quality=get_object_or_404(GreyQualityMaster,id=id)
    return render(request,'./GreyModule/GreyMaster/editGreyMasterQuality.html',{'id':id,'name':quality.quality_name})

def editGreyMasterQuality(request,id):
    quality=get_object_or_404(GreyQualityMaster,id=id)
    p=request.POST.get("edit-grey-quality")
    try:
        existing_quality=get_object_or_404(GreyQualityMaster,quality_name=p.upper())
        messages.error(request,"This quality already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/renderMasterQuality')
        p = p.upper()
        p = p.strip()
        quality.quality_name = p
        quality.save()
        messages.success(request,"Grey Quality Updated")

    return redirect('/renderGreyMasterQuality')

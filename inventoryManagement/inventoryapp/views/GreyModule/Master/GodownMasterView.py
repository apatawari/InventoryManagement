from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,GreyQualitiesMaster,GreyCheckingCutRatesMaster,GreyOutprocessAgenciesMaster,GreyGodownsMaster, GreyTransportAgenciesMaster, GreySuppliersMaster, Employee, GreyOrders, OrderStatus, LotStatus, GreyLots
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

####### GREY : Godown MASTER #######

def renderGreyMasterGodowns(request):
    all_grey_godowns = GreyGodownsMaster.objects.all().order_by('godown_name')
    paginator = Paginator(all_grey_godowns,10)
    page = request.GET.get('page')
    locations = paginator.get_page(page)
    return render(request,'./GreyModule/GreyMaster/masterGreyGodowns.html',{'records':locations})

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

    return render(request,'./GreyModule/GreyMaster/editGreyMasterGodown.html',{'id':id,'name':grey_godown.godown_name})

def editGreyMasterGodown(request,id):
    grey_godown = get_object_or_404(GreyGodownsMaster,id=id)
    godown_name = request.POST.get("edit-grey-godown")

    try:
        existing_party=get_object_or_404(GreyGodownsMaster,godown_name=godown_name)
        messages.error(request,"This Grey Godown already exists")
    except:
        if godown_name.strip()=="":
            messages.error(request,"Please enter valid input")
            return redirect('/renderGreyMasterGodowns')
        grey_godown.godown_name = godown_name
        grey_godown.save()
        messages.success(request,"Grey godown master is updated successfully")

    return redirect('/renderGreyMasterGodowns')

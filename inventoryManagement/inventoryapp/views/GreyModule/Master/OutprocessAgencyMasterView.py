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

###### GREY : Processing House Party Master #######

def renderGreyMasterOutprocessAgencies(request):
    parties_all = GreyOutprocessAgenciesMaster.objects.all().order_by('agency_name')

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./GreyModule/GreyMaster/masterGreyOutprocessAgencies.html',{'records':parties})

def saveGreyMasterOutprocessAgency(request):
    p = request.POST.get("outprocess-agency")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(GreyOutprocessAgenciesMaster,agency_name=p)
        messages.error(request,"This Outprocess Agency already exists")
    except:
        if p.strip()=="":
            messages.error(request,"Please enter valid input")
            return redirect('/renderGreyMasterOutprocessAgencies')
        new_Party = GreyOutprocessAgenciesMaster(
            agency_name= p
        )
        new_Party.save()
        messages.success(request,"Outprocess Agency added successfully")
    return redirect('/renderGreyMasterOutprocessAgencies')

def deleteGreyMasterOutprocessAgency(request,id):
    try:
        GreyOutprocessAgenciesMaster.objects.filter(id=id).delete()
        messages.success(request,"Outprocess Agency Deleted")
    except:
        messages.error(request,"Cannot delete this Outprocess Agency since it is being used")
    return redirect('/renderGreyMasterOutprocessAgencies')

def renderEditGreyMasterOutprocessAgency(request,id):
    party=get_object_or_404(GreyOutprocessAgenciesMaster,id=id)
    return render(request,'./GreyModule/GreyMaster/editGreyMasterOutprocessAgency.html',{'id':id,'name':party.agency_name})

def editGreyMasterOutprocessAgency(request,id):
    party=get_object_or_404(GreyOutprocessAgenciesMaster,id=id)
    p=request.POST.get("edit-outprocess-agency")

    try:
        existing_party=get_object_or_404(GreyOutprocessAgenciesMaster,agency_name=p)
        messages.error(request,"This Outprocess Agency already exists")
    except:
        if p.strip()=="":
            messages.error(request,"Please enter valid input")
            return redirect('/renderGreyMasterOutprocessAgencies')
        p = p.upper()
        p = p.strip()
        party.agency_name = p
        party.save()
        messages.success(request,"Outprocess Agency edited")

    return redirect('/renderGreyMasterOutprocessAgencies')

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


########## Transport Agency Master ###########

def renderGreyMasterTransportAgencies(request):
    parties_all = GreyTransportAgenciesMaster.objects.all().order_by('transport_agency_name')
    #return render(request,'./GreyModule/GreyMaster/addparty.html',{'parties':parties_all})

    paginator = Paginator(parties_all,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./GreyModule/GreyMaster/masterGreyTransportAgencies.html',{'records':parties})

def saveGreyMasterTransportAgency(request):
    transport_agency_name = request.POST.get("transport_agency_name")
    freight = request.POST.get("freight")
    transport_agency_name = transport_agency_name.upper().strip()

    try:
        existing_transport_agency=get_object_or_404(GreyTransportAgenciesMaster,transport_agency_name=transport_agency_name)
        messages.error(request,"This Transport Agency already exists")
    except:
        if transport_agency_name.strip()=="":
            messages.error(request,"please enter valid transport agency name")
            return redirect('/renderGreyMasterTransportAgencies')
        new_transport = GreyTransportAgenciesMaster(
            transport_agency_name = transport_agency_name ,
            freight=float(freight)
        )
        new_transport.save()
        messages.success(request,"Transport Agency added successfully")
    return redirect('/renderGreyMasterTransportAgencies')

def deleteGreyMasterTransportAgency(request,id):
    try:
        GreyTransportAgenciesMaster.objects.filter(id=id).delete()
        messages.success(request,"Transport Agency deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/renderGreyMasterTransportAgencies')

def renderEditGreyMasterTransportAgency(request,id):
    transport_agency=get_object_or_404(GreyTransportAgenciesMaster,id=id)
    return render(request,'./GreyModule/GreyMaster/editGreyMasterTransportAgencies.html',{'id':id,'transport_agency_name':transport_agency.transport_agency_name,'freight':transport_agency.freight})

def editGreyMasterTransportAgency(request,id):

    transport_agency=get_object_or_404(GreyTransportAgenciesMaster,id=id)
    transport_agency_name = request.POST.get("transport_agency_name")
    transport_agency_name = transport_agency_name.upper().strip()

    try:
        existing_transport_agency=get_object_or_404(GreyTransportAgenciesMaster,transport_agency_name=transport_agency_name)
        messages.error(request,"This Transport Agency already exists")
    except:

        transport_agency.transport_agency_name = transport_agency_name
        transport_agency.freight = float(request.POST.get('freight'))
        transport_agency.save()
        messages.success(request,"Transport Agency Updated Successfully")

    return redirect('/renderGreyMasterTransportAgencies')

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

############## SUPPLIER MASTER #############


def masterGreySuppliers(request):
    all_checker = GreySuppliersMaster.objects.all().order_by('supplier_name')
    paginator = Paginator(all_checker,10)
    page = request.GET.get('page')
    checkers = paginator.get_page(page)

    return render(request,'./GreyModule/GreyMaster/masterGreySuppliers.html',{'records':checkers})

def saveGreySupplier(request):

    supplier_name=(request.POST.get("supplier_name"))
    supplier_name.strip()
    m=request.POST.get("address")
    m = m.strip()
    n=request.POST.get("city")
    n = n.strip()
    o=request.POST.get("contact_number")
    o = o.strip()
    p=request.POST.get("email")
    p = p.strip()

    r=request.POST.get("remarks")
    r = r.strip()


    try:
        existing_supplier = get_object_or_404(GreySuppliersMaster,supplier_name=supplier_name.upper())
        messages.error(request,"This grey supplier already exists")
    except:
        if  supplier_name=="":
            messages.error(request,"please enter valid input")
            return redirect('masterGreySuppliers')
        new_quality = GreySuppliersMaster(
            supplier_name = supplier_name.upper(),
            city = n.upper(),
            address = m.upper(),
            email=p,
            contact_number=o,
            remarks=r.upper()

        )
        new_quality.save()
        messages.success(request,"Supplier added")
    return redirect('masterGreySuppliers')

def deleteGreySupplier(request,id):
    try:
        GreySuppliersMaster.objects.filter(id=id).delete()
        messages.success(request,"Supplier deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('masterGreySuppliers')

def renderEditGreySupplier(request,id):
    quality=get_object_or_404(GreySuppliersMaster,id=id)
    return render(request,'./GreyModule/GreyMaster/editGreyMasterSupplier.html',{'id':id,'record':quality})

def editGreySupplier(request,id):
    quality=get_object_or_404(GreySuppliersMaster,id=id)
    q=request.POST.get("id")

    supplier_name=request.POST.get("supplier_name")
    m=request.POST.get("city")
    o=request.POST.get("email")
    p=request.POST.get("contact_number")
    r=request.POST.get("remarks")

    try:
        existing_supplier = get_object_or_404(GreySuppliersMaster,supplier_name=supplier_name.upper())
        messages.error(request,"This grey supplier already exists")

    except:
        if supplier_name=="":
            messages.error(request,"Please atleast input the supplier name")
            return redirect('masterGreySuppliers')
        quality.id = q
        quality.supplier_name = supplier_name
        quality.city = m
        quality.email = o
        quality.contact_number = p
        quality.remarks = r
        quality.save()
        messages.success(request,"Supplier Details Updated")
    return redirect('masterGreySuppliers')


##################################### GREY Supplier  MASTER END ###########################################

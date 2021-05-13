from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,GreyQualitiesMaster, GreyTransportAgenciesMaster, GreySuppliersMaster, GreyOrders, OrderStatus
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

############## ORDERS #############

def greyOrders(request):
    return redirect('/ordersList')

def editGreyOrder(request):
    order_number=request.POST.get("order_number")
    order_date=request.POST.get("order_date")
    supplier=(request.POST.get("supplier_name"))
    quality=request.POST.get("quality")
    quality = quality.strip()
    avg_cut=request.POST.get("avg_cut")
    thans=request.POST.get("thans")
    # rate=request.POST.get("rate")
    remarks=request.POST.get("remarks")
    remarks = remarks.strip()
    print(supplier)
    if  order_date=="" or supplier=="" or quality=="" or thans=="" or avg_cut=="":
        messages.error(request,"Please fill all the fields")
        return redirect('/ordersList')
    qualityObject = GreyQualitiesMaster.objects.get(quality_name=quality)
    supplierObject = GreySuppliersMaster.objects.get(supplier_name=supplier)
    print(supplierObject.supplier_name)
    old_order = GreyOrders.objects.get(order_number=order_number)
    old_order.grey_supplier = supplierObject
    old_order.grey_quality = qualityObject
    old_order.order_date = order_date
    old_order.thans = thans
    # old_order.rate = rate
    old_order.remarks = remarks
    old_order.avg_cut = avg_cut
    old_order.save()
    messages.success(request,"Order Updated")
    return redirect('/ordersList')

def ordersList(request):
    orderList = GreyOrders.objects.all().order_by('order_number')
    suppliers = GreySuppliersMaster.objects.all()
    qualities = GreyQualitiesMaster.objects.all()
    transport_agencies = GreyTransportAgenciesMaster.objects.all()
    paginator = Paginator(orderList,10)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    return render(request,'./GreyModule/GreyOrders/greyOrders.html',{'records':orders,'suppliers':suppliers, 'quality':qualities, 'transport_agencies':transport_agencies})

def filteredOrdersList(request):
    quality=request.POST.get("filterQuality")
    print(quality)
    if quality == "":
        return redirect('/ordersList')
    qualityObject = GreyQualitiesMaster.objects.get(quality_name=quality)
    orderList = GreyOrders.objects.filter(grey_quality=qualityObject).order_by('order_number')
    suppliers = GreySuppliersMaster.objects.all()
    qualities = GreyQualitiesMaster.objects.all()
    paginator = Paginator(orderList,10)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    return render(request,'./GreyModule/GreyOrders/greyOrders.html',{'records':orders,'suppliers':suppliers, 'quality':qualities, 'filterQuality':quality})

def placeNewGreyOrder(request):
    order_date=request.POST.get("order_date")
    supplier=(request.POST.get("supplier_name"))
    quality=request.POST.get("quality")
    quality = quality.strip()
    thans=request.POST.get("thans")
    remarks=request.POST.get("remarks")
    remarks = remarks.strip()

    if  order_date=="" or supplier=="" or quality=="" or thans=="":
        messages.error(request,"Please fill all the fields")
        return redirect('/ordersList')

    qualityObject = GreyQualitiesMaster.objects.get(quality_name=quality)
    supplierObject = GreySuppliersMaster.objects.get(supplier_name=supplier)
    qualityObject = GreyQualitiesMaster.objects.get(quality_name=quality)
    new_status = OrderStatus()
    new_status.type="Initial State"
    new_status.save()
    new_order = GreyOrders(
            order_date = order_date,
            thans =thans,
            grey_quality=qualityObject,
            grey_supplier= supplierObject,
            # rate=rate,
            remarks=remarks,
            order_status = new_status,
            avg_cut=avg_cut
        )
    new_order.save()
    messages.success(request,"Order Placed")
    return redirect('/ordersList')

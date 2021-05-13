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


######### GREY - CUT RANGE MASTER ########

def renderGreyMasterCheckingCutRates(request):
    all_cut_ranges = GreyCheckingCutRatesMaster.objects.all().order_by('cut_start_range')
    paginator = Paginator(all_cut_ranges,10)
    page = request.GET.get('page')
    cut_ranges = paginator.get_page(page)
    return render(request,'./GreyModule/GreyMaster/masterGreyCheckingCutRates.html',{'records':cut_ranges})

def saveGreyMasterCheckingCutRate(request):
    start_range = float(request.POST.get("cut_start_range"))
    end_range = float(request.POST.get("cut_end_range"))
    existingrange = GreyCheckingCutRatesMaster.objects.all()
    flag = 0

    for i in existingrange:
        if i.cut_start_range == start_range or end_range == i.cut_end_range or end_range == i.cut_start_range or i.cut_end_range == start_range :
            flag = flag + 1
            break

    if flag == 0:

        newRecord = GreyCheckingCutRatesMaster(
            cut_start_range = start_range,
            cut_end_range = end_range,
            checking_rate = float(request.POST.get('rate'))
        )

        newRecord.save()
        messages.success(request,'Range added')
        return redirect('/renderGreyMasterCheckingCutRates')

    else:

        messages.error(request,'Range already exists')
        return redirect('/renderGreyMasterCheckingCutRates')

def deleteGreyMasterCheckingCutRate(request,id):
    GreyCheckingCutRatesMaster.objects.filter(id=id).delete()
    messages.success(request,"Range deleted")
    return redirect('/renderGreyMasterCheckingCutRates')

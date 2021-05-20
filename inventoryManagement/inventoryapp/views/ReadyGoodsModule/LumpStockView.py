from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record, GreyQualityMaster, SalesQualityMaster
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

def renderLumpStock(request):
    lumpStock = LumpStock.objects.all().order_by(SalesQualityMaster.sales_quality_name)
    paginator = Paginator(lumpStock,10)
    page = request.GET.get('page')
    lumpStock = paginator.get_page(page)
    return render(request,'./ReadyGoodsModule/LumpStock/lumpStock.html',{'records':lumpStock})

def saveLumpStock(request):
    felt_book_number = request.POST.get("felt_book_number")
    design_number = request.POST.get("design_number")

    from_felt_thans = request.POST.get("from_felt_thans")
    from_felt_tp = request.POST.get("from_felt_tp")
    from_felt_date = request.POST.get("from_felt_date")

    in_packing_thans = request.POST.get("in_packing_thans")
    in_packing_tp   = request.POST.get("in_packing_tp")
    in_packing_date = request.POST.get("in_packing_date")

    grey_quality_id = request.POST.get("grey_quality_id")
    sales_quality_id = request.POST.get("sales_quality_id")

    return redirect('/renderGreyMasterQuality')

def editLumpStock(request):
    design_number = request.POST.get("design_number")
    from_felt_thans = request.POST.get("from_felt_thans")
    in_packing_thans = request.POST.get("in_packing_thans")
    grey_quality_id = request.POST.get("grey_quality_id")
    sales_quality_id = request.POST.get("sales_quality_id")

    return redirect('/renderGreyMasterQuality')

def renderEditLumpStock(request):
    design_number = request.POST.get("design_number")
    from_felt_thans = request.POST.get("from_felt_thans")
    in_packing_thans = request.POST.get("in_packing_thans")
    grey_quality_id = request.POST.get("grey_quality_id")
    sales_quality_id = request.POST.get("sales_quality_id")

    return redirect('/renderGreyMasterQuality')

def deleteLumpStock(request):
    design_number = request.POST.get("design_number")
    from_felt_thans = request.POST.get("from_felt_thans")
    in_packing_thans = request.POST.get("in_packing_thans")
    grey_quality_id = request.POST.get("grey_quality_id")
    sales_quality_id = request.POST.get("sales_quality_id")

    return redirect('/renderGreyMasterQuality')

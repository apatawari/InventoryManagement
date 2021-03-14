from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,GreyQualityMaster,GreyCheckerMaster,GreyCutRange,ProcessingPartyNameMaster,GreyArrivalLocationMaster,ColorAndChemicalsSupplier,Color,ColorRecord,ChemicalsDailyConsumption,ChemicalsAllOrders,ChemicalsGodownLooseMergeStock,ChemicalsGodownsMaster,ChemicalsLooseGodownMaster,ChemicalsUnitsMaster,ChemicalsClosingStock
from inventoryapp.models import Employee,CompanyAccounts,ChemicalsClosingStockperGodown,MonthlyPayment,GreyTransportMaster,CityMaster,EmployeeCategoryMaster
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


##### HOMEPAGE #####
def index(request):
    recs=ChemicalsAllOrders.objects.all()
    idlist=[]
    for r in recs:
        try:
            dups=get_list_or_404(ChemicalsAllOrders,order_no=r.order_no,color=r.color,unit=r.unit,state="Ordered")
            flag=0
            for d in dups:
                if flag==0:
                    flag=1
                else:
                    idlist.append(d.id)

        except:
            pass

    colrecs=ColorRecord.objects.all()
    idlist2=[]
    for r in colrecs:
        try:
            dups=get_list_or_404(ColorRecord,order_no=r.order_no,color=r.color,unit=r.unit,state="Ordered")
            flag=0
            for d in dups:
                if flag==0:
                    flag=1
                else:
                    idlist2.append(d.id)

        except:
            pass

    for i in idlist:
        ChemicalsAllOrders.objects.filter(id=i).delete()
    for i in idlist2:
        ColorRecord.objects.filter(id=i).delete()

    return render(request, 'index.html')

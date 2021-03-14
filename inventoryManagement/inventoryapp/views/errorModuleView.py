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

####### EVENT HANDLERS ########
# Bad Request 400
def bad_request(request, exception):
    response = render('./error/400.html', context_instance=RequestContext(request))
    response.status_code = 400

    return response

# Permission Denied 403
def permission_denied(request, exception):
    response = render('./error/403.html', context_instance=RequestContext(request))
    response.status_code = 403

    return response

# Page Not Found 404
def page_not_found(request, exception):
    response = render('./error/404.html', context_instance=RequestContext(request))
    response.status_code = 404

    return response

# HTTP Error 500
def server_error(request):
    response = render('./error/500.html', context_instance=RequestContext(request))
    response.status_code = 500

    return response

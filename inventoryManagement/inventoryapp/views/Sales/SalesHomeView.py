from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,SalesQualityMaster
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

def salesHome(request):
    return render(request, './SalesModule/SalesHome/salesHome.html')

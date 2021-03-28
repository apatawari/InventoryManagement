from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from django.http import HttpResponse,QueryDict
from django.core.paginator import Paginator
from django.template import RequestContext
from inventoryapp.models import Record,GreyQualitiesMaster,GreyCheckingCutRatesMaster,GreyOutprocessAgenciesMaster,GreyGodownsMaster,ColorAndChemicalsSupplier,Color,ColorRecord,ChemicalsDailyConsumption,ChemicalsAllOrders,ChemicalsGodownLooseMergeStock,ChemicalsGodownsMaster,ChemicalsLooseGodownMaster,ChemicalsUnitsMaster,ChemicalsClosingStock
from inventoryapp.models import Employee,CompanyAccounts,ChemicalsClosingStockperGodown,MonthlyPayment,GreyTransportAgenciesMaster,CityMaster,EmployeeCategoryMaster
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




###########################################     COLOR & CHEMICAL TAB   #################################################

####### COLOR - SUPPLIER MASTER ########
def renderAddColorSupplier(request):
    suppliers=ColorAndChemicalsSupplier.objects.all().order_by('supplier')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/colorsupplier.html',{'suppliers':parties})

def colorhome(request):
    return render(request, './ColorChemicalModule/colorhome.html')

def saveSupplier(request):
    p = request.POST.get("supplier")
    p = p.upper()
    p = p.strip()

    c = request.POST.get("city")
    c = c.upper()
    c = c.strip()

    a = request.POST.get("address")
    a = a.upper()
    a = a.strip()
    try:
        existing_party=get_object_or_404(ColorAndChemicalsSupplier,supplier=p,city=c,address=a)
        messages.error(request,"This Supplier Party already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addcolorsupplier')
        new_Party = ColorAndChemicalsSupplier(
            supplier = p,
            address=a,
            city=c
        )
        new_Party.save()
        messages.success(request,"Supplier Party added successfully")
    return redirect('/addcolorsupplier')

def deleteSupplier(request,id):
    try:
        ColorAndChemicalsSupplier.objects.filter(id=id).delete()
        messages.success(request,"Supplier Party deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addcolorsupplier')

def renderEditSupplier(request,id):
    party=get_object_or_404(ColorAndChemicalsSupplier,id=id)
    return render(request,'./ColorChemicalModule/editsupplier.html',{'id':id,'name':party.supplier})

def editSupplier(request,id):
    party=get_object_or_404(ColorAndChemicalsSupplier,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.supplier = p
    party.save()
    messages.success(request,"Supplier Party edited")
    return redirect('/addcolorsupplier')


#################### Color - ADD CHEMICAL/COLOR MASTER ################
def renderAddColor(request):
    suppliers=Color.objects.all().order_by('color')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/addcolor.html',{'suppliers':parties})

def saveColor(request):
    p = request.POST.get("color")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(Color,color=p)
        messages.error(request,"This Color already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addcolor')
        new_Party = Color(
            color = p
        )
        new_Party.save()
        messages.success(request,"Color added successfully")
    return redirect('/addcolor')

def deleteColor(request,id):
    try:
        Color.objects.filter(id=id).delete()
        messages.success(request,"Color deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addcolor')

def renderEditColor(request,id):
    party=get_object_or_404(Color,id=id)
    return render(request,'./ColorChemicalModule/editcolor.html',{'id':id,'name':party.color})

def editColor(request,id):
    party=get_object_or_404(Color,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.color = p
    party.save()
    messages.success(request,"Color edited")
    return redirect('/addcolor')

########### Add COLOR & CHEMICAL - Godown #############
def renderAddGodown(request):
    suppliers=ChemicalsGodownsMaster.objects.all().order_by('godown')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/addgodown.html',{'suppliers':parties})

def saveGodown(request):
    p = request.POST.get("godown")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(ChemicalsGodownsMaster,godown=p)
        messages.error(request,"This Godown already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addgodown')
        new_Party = ChemicalsGodownsMaster(
            godown = p
        )
        new_Party.save()
        messages.success(request,"Godown added successfully")
    return redirect('/addgodown')

def deleteGodown(request,id):
    try:
        ChemicalsGodownsMaster.objects.filter(id=id).delete()
        messages.success(request,"Godown deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addgodown')

def renderEditGodown(request,id):
    party=get_object_or_404(ChemicalsGodownsMaster,id=id)
    return render(request,'./ColorChemicalModule/editgodown.html',{'id':id,'name':party.godown})

def editGodown(request,id):
    party=get_object_or_404(ChemicalsGodownsMaster,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.godown = p
    party.save()
    messages.success(request,"Godown edited")
    return redirect('/addgodown')

########### Add COLOR & CHEMICAL - Loose Godown #############

def renderAddLease(request):
    suppliers=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/addlease.html',{'suppliers':parties})

def saveLease(request):
    p = request.POST.get("lease")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(ChemicalsLooseGodownMaster,lease=p)
        messages.error(request,"This Loose already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addlease')
        new_Party = ChemicalsLooseGodownMaster(
            lease = p
        )
        new_Party.save()
        messages.success(request,"Lease added successfully")
    return redirect('/addlease')

def deleteLease(request,id):
    try:
        ChemicalsLooseGodownMaster.objects.filter(id=id).delete()
        messages.success(request,"Lease deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addlease')

def renderEditLease(request,id):
    party=get_object_or_404(ChemicalsLooseGodownMaster,id=id)
    return render(request,'./ColorChemicalModule/editlease.html',{'id':id,'name':party.lease})

def editLease(request,id):
    party=get_object_or_404(ChemicalsLooseGodownMaster,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.lease = p
    party.save()
    messages.success(request,"Loose edited")
    return redirect('/addlease')


########### ADD COLOR & CHEMICAL - UNIT MASTER #############
def renderAddUnit(request):
    suppliers=ChemicalsUnitsMaster.objects.all().order_by('unit')
    paginator = Paginator(suppliers,10)
    page = request.GET.get('page')
    parties = paginator.get_page(page)
    return render(request,'./ColorChemicalModule/addunit.html',{'suppliers':parties})

def saveUnit(request):
    p = request.POST.get("unit")
    p = p.upper()
    p = p.strip()
    try:
        existing_party=get_object_or_404(ChemicalsUnitsMaster,unit=p)
        messages.error(request,"This Unit already exists")
    except:
        if p.strip()=="":
            messages.error(request,"please enter valid input")
            return redirect('/addunit')
        new_Party = ChemicalsUnitsMaster(
            unit = p
        )
        new_Party.save()
        messages.success(request,"Unit added successfully")
    return redirect('/addunit')

def deleteUnit(request,id):
    try:
        ChemicalsUnitsMaster.objects.filter(id=id).delete()
        messages.success(request,"Unit deleted")
    except:
        messages.error(request,"Cannot delete this master since it is being used")
    return redirect('/addunit')

def renderEditUnit(request,id):
    party=get_object_or_404(ChemicalsUnitsMaster,id=id)
    return render(request,'./ColorChemicalModule/editunit.html',{'id':id,'name':party.unit})

def editUnit(request,id):
    party=get_object_or_404(ChemicalsUnitsMaster,id=id)
    p=request.POST.get("edit-party")
    p = p.upper()
    p = p.strip()
    party.unit = p
    party.save()
    messages.success(request,"Unit edited")
    return redirect('/addunit')

########### Place order for COLOR & CHEMICAL #############

def placeOrder(request):
    color=Color.objects.all().order_by("color")
    suppliers=ColorAndChemicalsSupplier.objects.all().order_by('supplier')
    units=ChemicalsUnitsMaster.objects.all().order_by('unit')

    d=datetime.date.today()
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    d=str(d)
    try:
        rec = ColorRecord.objects.all().order_by('-order_no')[0]
        order_no=rec.order_no + 1
    except:
        order_no = 1
    return render(request,'./ColorChemicalModule/placeorder.html',{'color':color,'suppliers':suppliers,'units':units,'date':d,'maxdate':maxdate,'orderno':order_no})

def saveOrder(request):
    color_unit=[]
    q=float(request.POST.get('quantity'))
    r=float(request.POST.get('rate'))
    a=round(q*r,2)
    new_order=ColorRecord(
        color=get_object_or_404(Color,id=int(request.POST.get('color'))),
        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
        order_no=request.POST.get('order_no'),
        order_date=str(request.POST.get('order_date')),
        rate=request.POST.get('rate'),
        amount=a,
        quantity=request.POST.get('quantity'),
        state="Ordered",
        recieving_date=None,
        total_quantity = request.POST.get('quantity'),
        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit')))
    )
    new_order.save()

    new_order=ChemicalsAllOrders(
        color=get_object_or_404(Color,id=int(request.POST.get('color'))),
        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
        order_no=request.POST.get('order_no'),
        order_date=str(request.POST.get('order_date')),
        rate=request.POST.get('rate'),
        amount=a,
        quantity=request.POST.get('quantity'),
        state="Ordered",
        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit'))),
        rem_quantity=request.POST.get('quantity')
    )
    new_order.save()
    l=[request.POST.get('color'),request.POST.get('unit')]
    color_unit.append(l)
    if(request.POST.get('rate2')!='' and request.POST.get('quantity2')!='' and request.POST.get('color2')!=''):
        q=float(request.POST.get('quantity2'))
        r=float(request.POST.get('rate2'))
        a=round(q*r,2)
        l=[request.POST.get('color2'),request.POST.get('unit2')]
        if l in color_unit:
            messages.error(request,"Color Repeated. Order placed partially till first color")
            return redirect('/placeorder')
        color_unit.append(l)
        new_order=ColorRecord(
            color=get_object_or_404(Color,id=int(request.POST.get('color2'))),
            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
            order_no=request.POST.get('order_no'),
            order_date=str(request.POST.get('order_date')),
            rate=request.POST.get('rate2'),
            amount=a,
            quantity=request.POST.get('quantity2'),
            state="Ordered",
            recieving_date=None,
            total_quantity = request.POST.get('quantity2'),
            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit2')))
        )
        new_order.save()

        new_order=ChemicalsAllOrders(
            color=get_object_or_404(Color,id=int(request.POST.get('color2'))),
            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
            order_no=request.POST.get('order_no'),
            order_date=str(request.POST.get('order_date')),
            rate=request.POST.get('rate2'),
            amount=a,
            quantity=request.POST.get('quantity2'),
            state="Ordered",
            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit2'))),
            rem_quantity=request.POST.get('quantity2')
        )
        new_order.save()

        if(request.POST.get('rate3')!='' and request.POST.get('quantity3')!='' and request.POST.get('color3')!=''):
            q=float(request.POST.get('quantity3'))
            r=float(request.POST.get('rate3'))
            a=round(q*r,2)
            l=[request.POST.get('color3'),request.POST.get('unit3')]
            if l in color_unit:
                messages.error(request,"Color Repeated. Order placed partially till second color")
                return redirect('/placeorder')
            color_unit.append(l)
            new_order=ColorRecord(
                color=get_object_or_404(Color,id=int(request.POST.get('color3'))),
                supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                order_no=request.POST.get('order_no'),
                order_date=str(request.POST.get('order_date')),
                rate=request.POST.get('rate3'),
                amount=a,
                quantity=request.POST.get('quantity3'),
                state="Ordered",
                recieving_date=None,
                total_quantity = request.POST.get('quantity3'),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit3')))
            )
            new_order.save()

            new_order=ChemicalsAllOrders(
                color=get_object_or_404(Color,id=int(request.POST.get('color3'))),
                supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                order_no=request.POST.get('order_no'),
                order_date=str(request.POST.get('order_date')),
                rate=request.POST.get('rate3'),
                amount=a,
                quantity=request.POST.get('quantity3'),
                state="Ordered",
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit3'))),
                rem_quantity=request.POST.get('quantity3')
            )
            new_order.save()

            if(request.POST.get('rate4')!='' and request.POST.get('quantity4')!='' and request.POST.get('color4')!=''):
                q=float(request.POST.get('quantity4'))
                r=float(request.POST.get('rate4'))
                a=round(q*r,2)
                l=[request.POST.get('color4'),request.POST.get('unit4')]
                if l in color_unit:
                    messages.error(request,"Color Repeated. Order placed partially till third color")
                    return redirect('/placeorder')
                color_unit.append(l)
                new_order=ColorRecord(
                    color=get_object_or_404(Color,id=int(request.POST.get('color4'))),
                    supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                    order_no=request.POST.get('order_no'),
                    order_date=str(request.POST.get('order_date')),
                    rate=request.POST.get('rate4'),
                    amount=a,
                    quantity=request.POST.get('quantity4'),
                    state="Ordered",
                    recieving_date=None,
                    total_quantity = request.POST.get('quantity4'),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit4')))
                )
                new_order.save()

                new_order=ChemicalsAllOrders(
                    color=get_object_or_404(Color,id=int(request.POST.get('color4'))),
                    supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                    order_no=request.POST.get('order_no'),
                    order_date=str(request.POST.get('order_date')),
                    rate=request.POST.get('rate4'),
                    amount=a,
                    quantity=request.POST.get('quantity4'),
                    state="Ordered",
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit4'))),
                    rem_quantity=request.POST.get('quantity4')
                )
                new_order.save()

                if(request.POST.get('rate5')!='' and request.POST.get('quantity5')!='' and request.POST.get('color5')!=''):
                    q=float(request.POST.get('quantity5'))
                    r=float(request.POST.get('rate5'))
                    a=round(q*r,2)
                    l=[request.POST.get('color5'),request.POST.get('unit5')]
                    if l in color_unit:
                        messages.error(request,"Color Repeated. Order placed partially till fourth color")
                        return redirect('/placeorder')
                    color_unit.append(l)
                    new_order=ColorRecord(
                        color=get_object_or_404(Color,id=int(request.POST.get('color5'))),
                        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                        order_no=request.POST.get('order_no'),
                        order_date=str(request.POST.get('order_date')),
                        rate=request.POST.get('rate5'),
                        amount=a,
                        quantity=request.POST.get('quantity5'),
                        state="Ordered",
                        recieving_date=None,
                        total_quantity = request.POST.get('quantity5'),
                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit5')))
                    )
                    new_order.save()

                    new_order=ChemicalsAllOrders(
                        color=get_object_or_404(Color,id=int(request.POST.get('color5'))),
                        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                        order_no=request.POST.get('order_no'),
                        order_date=str(request.POST.get('order_date')),
                        rate=request.POST.get('rate5'),
                        amount=a,
                        quantity=request.POST.get('quantity5'),
                        state="Ordered",
                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit5'))),
                        rem_quantity=request.POST.get('quantity5')
                    )
                    new_order.save()

                    if(request.POST.get('rate6')!='' and request.POST.get('quantity6')!='' and request.POST.get('color6')!=''):
                        q=float(request.POST.get('quantity6'))
                        r=float(request.POST.get('rate6'))
                        a=round(q*r,2)
                        l=[request.POST.get('color6'),request.POST.get('unit6')]
                        if l in color_unit:
                            messages.error(request,"Color Repeated. Order placed partially till fifth color")
                            return redirect('/placeorder')
                        color_unit.append(l)
                        new_order=ColorRecord(
                            color=get_object_or_404(Color,id=int(request.POST.get('color6'))),
                            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                            order_no=request.POST.get('order_no'),
                            order_date=str(request.POST.get('order_date')),
                            rate=request.POST.get('rate6'),
                            amount=a,
                            quantity=request.POST.get('quantity6'),
                            state="Ordered",
                            recieving_date=None,
                            total_quantity = request.POST.get('quantity6'),
                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit6')))
                        )
                        new_order.save()

                        new_order=ChemicalsAllOrders(
                            color=get_object_or_404(Color,id=int(request.POST.get('color6'))),
                            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                            order_no=request.POST.get('order_no'),
                            order_date=str(request.POST.get('order_date')),
                            rate=request.POST.get('rate6'),
                            amount=a,
                            quantity=request.POST.get('quantity6'),
                            state="Ordered",
                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit6'))),
                            rem_quantity=request.POST.get('quantity6')
                        )
                        new_order.save()

                        if(request.POST.get('rate7')!='' and request.POST.get('quantity7')!='' and request.POST.get('color7')!=''):
                            q=float(request.POST.get('quantity7'))
                            r=float(request.POST.get('rate7'))
                            a=round(q*r,2)
                            l=[request.POST.get('color7'),request.POST.get('unit7')]
                            if l in color_unit:
                                messages.error(request,"Color Repeated. Order placed partially till sixth color")
                                return redirect('/placeorder')
                            color_unit.append(l)
                            new_order=ColorRecord(
                                color=get_object_or_404(Color,id=int(request.POST.get('color7'))),
                                supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                order_no=request.POST.get('order_no'),
                                order_date=str(request.POST.get('order_date')),
                                rate=request.POST.get('rate7'),
                                amount=a,
                                quantity=request.POST.get('quantity7'),
                                state="Ordered",
                                recieving_date=None,
                                total_quantity = request.POST.get('quantity7'),
                                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit7')))
                            )
                            new_order.save()

                            new_order=ChemicalsAllOrders(
                                color=get_object_or_404(Color,id=int(request.POST.get('color7'))),
                                supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                order_no=request.POST.get('order_no'),
                                order_date=str(request.POST.get('order_date')),
                                rate=request.POST.get('rate7'),
                                amount=a,
                                quantity=request.POST.get('quantity7'),
                                state="Ordered",
                                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit7'))),
                                rem_quantity=request.POST.get('quantity7')

                            )
                            new_order.save()

                            if(request.POST.get('rate8')!='' and request.POST.get('quantity8')!='' and request.POST.get('color8')!=''):
                                q=float(request.POST.get('quantity8'))
                                r=float(request.POST.get('rate8'))
                                a=round(q*r,2)
                                l=[request.POST.get('color8'),request.POST.get('unit8')]
                                if l in color_unit:
                                    messages.error(request,"Color Repeated. Order placed partially till seventh color")
                                    return redirect('/placeorder')
                                color_unit.append(l)
                                new_order=ColorRecord(
                                    color=get_object_or_404(Color,id=int(request.POST.get('color8'))),
                                    supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                    order_no=request.POST.get('order_no'),
                                    order_date=str(request.POST.get('order_date')),
                                    rate=request.POST.get('rate8'),
                                    amount=a,
                                    quantity=request.POST.get('quantity8'),
                                    state="Ordered",
                                    recieving_date=None,
                                    total_quantity = request.POST.get('quantity8'),
                                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit8')))
                                )
                                new_order.save()

                                new_order=ChemicalsAllOrders(
                                    color=get_object_or_404(Color,id=int(request.POST.get('color8'))),
                                    supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                    order_no=request.POST.get('order_no'),
                                    order_date=str(request.POST.get('order_date')),
                                    rate=request.POST.get('rate8'),
                                    amount=a,
                                    quantity=request.POST.get('quantity8'),
                                    state="Ordered",
                                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit8'))),
                                    rem_quantity=request.POST.get('quantity8')
                                )
                                new_order.save()

                                if(request.POST.get('rate9')!='' and request.POST.get('quantity9')!='' and request.POST.get('color9')!=''):
                                    q=float(request.POST.get('quantity9'))
                                    r=float(request.POST.get('rate9'))
                                    a=round(q*r,2)
                                    l=[request.POST.get('color9'),request.POST.get('unit9')]
                                    if l in color_unit:
                                        messages.error(request,"Color Repeated. Order placed partially till eight color")
                                        return redirect('/placeorder')
                                    color_unit.append(l)
                                    new_order=ColorRecord(
                                        color=get_object_or_404(Color,id=int(request.POST.get('color9'))),
                                        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                        order_no=request.POST.get('order_no'),
                                        order_date=str(request.POST.get('order_date')),
                                        rate=request.POST.get('rate9'),
                                        amount=a,
                                        quantity=request.POST.get('quantity9'),
                                        state="Ordered",
                                        recieving_date=None,
                                        total_quantity = request.POST.get('quantity9'),
                                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit9')))
                                    )
                                    new_order.save()

                                    new_order=ChemicalsAllOrders(
                                        color=get_object_or_404(Color,id=int(request.POST.get('color9'))),
                                        supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                        order_no=request.POST.get('order_no'),
                                        order_date=str(request.POST.get('order_date')),
                                        rate=request.POST.get('rate9'),
                                        amount=a,
                                        quantity=request.POST.get('quantity9'),
                                        state="Ordered",
                                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit9'))),
                                        rem_quantity=request.POST.get('quantity9')
                                    )
                                    new_order.save()

                                    if(request.POST.get('rate10')!='' and request.POST.get('quantity10')!='' and request.POST.get('color10')!=''):
                                        q=float(request.POST.get('quantity10'))
                                        r=float(request.POST.get('rate10'))
                                        a=round(q*r,2)
                                        l=[request.POST.get('color10'),request.POST.get('unit10')]
                                        if l in color_unit:
                                            messages.error(request,"Color Repeated. Order placed partially till ninth color")
                                            return redirect('/placeorder')

                                        new_order=ColorRecord(
                                            color=get_object_or_404(Color,id=int(request.POST.get('color10'))),
                                            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                            order_no=request.POST.get('order_no'),
                                            order_date=str(request.POST.get('order_date')),
                                            rate=request.POST.get('rate10'),
                                            amount=a,
                                            quantity=request.POST.get('quantity10'),
                                            state="Ordered",
                                            recieving_date=None,
                                            total_quantity = request.POST.get('quantity10'),
                                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit10')))
                                        )
                                        new_order.save()

                                        new_order=ChemicalsAllOrders(
                                            color=get_object_or_404(Color,id=int(request.POST.get('color10'))),
                                            supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier'))),
                                            order_no=request.POST.get('order_no'),
                                            order_date=str(request.POST.get('order_date')),
                                            rate=request.POST.get('rate10'),
                                            amount=a,
                                            quantity=request.POST.get('quantity10'),
                                            state="Ordered",
                                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit10'))),
                                            rem_quantity=request.POST.get('quantity10')
                                        )
                                        new_order.save()
    messages.success(request,'Order has been Placed')
    return redirect('/placeorder')

########### DISPLAY PLACED COLOR & CHEMICAL ORDERS #############
def orderGeneration(request):
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


    rec=ChemicalsAllOrders.objects.all().order_by('-state','order_no')
    records_filter = ColorOrderFilter(request.GET,queryset=rec)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    suppliers=ColorAndChemicalsSupplier.objects.all().order_by('supplier')
    colors=Color.objects.all().order_by('color')

    return render(request,'./ColorChemicalModule/ordergeneration.html',{'records':records,'filter':records_filter,'suppliers':suppliers,'colors':colors})

def orderEdit(request,id):
    rec=get_object_or_404(ChemicalsAllOrders, id=id)
    try:
        #rec2=get_object_or_404(ColorRecord,rate=rec.rate,order_no=rec.order_no,color=rec.color,unit=rec.unit,state="Ordered")

        orderdate=str(rec.order_date)
        color = Color.objects.all().order_by('color')
        supplier = ColorAndChemicalsSupplier.objects.all().order_by('supplier')
        unit = ChemicalsUnitsMaster.objects.all().order_by('unit')
        return render(request, './ColorChemicalModule/editorder.html',{'record':rec,'orderdate':orderdate,'color':color,'suppliers':supplier,'units':unit})
    except:
        messages.error(request,"This order has been recieved")
        return redirect('/ordergeneration')

def orderDelete(request,id):
    rec=get_object_or_404(ChemicalsAllOrders, id=id)
    rec2=get_object_or_404(ColorRecord,order_no=rec.order_no,color=rec.color,unit=rec.unit)
    rec.delete()
    rec2.delete()
    return redirect('/ordergeneration')

def orderEditSave(request,id):
    rec_order=get_object_or_404(ChemicalsAllOrders, id=id)
    q=float(request.POST.get('quantity'))
    r=float(request.POST.get('rate'))
    a=q*r
    a=round(a,2)
    orderno=rec_order.order_no
    color = rec_order.color
    unit=rec_order.unit
    rate=rec_order.rate
    try:
        rec=get_object_or_404(ColorRecord, rate=rate,order_no=orderno,color=color,unit=unit,state="Ordered")
        rec.supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier')))
        rec.color=get_object_or_404(Color,id=int(request.POST.get('color')))
        rec.order_date=str(request.POST.get('order_date'))
        rec.rate=request.POST.get('rate')
        rec.amount=a
        rec.quantity=request.POST.get('quantity')
        rec.total_quantity = request.POST.get('quantity')
        rec.unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit')))
        rec.save()
    finally:
        rec_order.supplier=get_object_or_404(ColorAndChemicalsSupplier,id=int(request.POST.get('supplier')))
        rec_order.color=get_object_or_404(Color,id=int(request.POST.get('color')))
        rec_order.order_date=str(request.POST.get('order_date'))
        rec_order.rate=request.POST.get('rate')
        rec_order.amount=a
        rec_order.quantity=request.POST.get('quantity')
        rec_order.rem_quantity=request.POST.get('quantity')
        rec_order.unit = get_object_or_404(ChemicalsUnitsMaster,id=int(request.POST.get('unit')))
        rec_order.save()
    return redirect('/ordergeneration')


########### DISPLAY COLOR & CHEMICAL COMBINED STOCK IN GODOWN ############

def goodsReceived(request):
    godowns=ChemicalsGodownsMaster.objects.all()
    godowns_list=[]
    for g in godowns:
        godowns_list.append(g)

    godown_colors = ChemicalsGodownLooseMergeStock.objects.filter(state__in=godowns_list,loose_godown_state=None).exclude(quantity=0)
    # rec=ColorRecord.objects.filter(state='Godown').order_by('godown','color')
    records_filter = GodownLeaseFilter(request.GET,queryset=godown_colors)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    chemicals=Color.objects.all().order_by('color')
    godowns=ChemicalsGodownsMaster.objects.all().order_by('godown')

    return render(request,'./ColorChemicalModule/goodsreceived.html',{'filter':records_filter,'colors':records,'Godown':"Godown Containing",'chemicals':chemicals,'godowns':godowns})

def goodsRequest(request):
    rec=ColorRecord.objects.filter(state='Ordered').order_by('order_no')
    records_filter = ColorFilter(request.GET,queryset=rec)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request,'./ColorChemicalModule/goodsrequest.html',{'records':records,'filter':records_filter})

def goods(request,id):
    ogorder=get_object_or_404(ChemicalsAllOrders, id=id)
    rec=get_object_or_404(ColorRecord, order_no=ogorder.order_no,state="Ordered",color = ogorder.color, unit = ogorder.unit)

    mindate=str(rec.order_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')
    d=datetime.date.today()
    d=str(d)
    orderdate=str(rec.order_date)
    godowns = ChemicalsGodownsMaster.objects.all().order_by('godown')
    return render(request, './ColorChemicalModule/goodsapprove.html', {'date':d,'record':rec,'mindate':mindate,'maxdate':maxdate,'orderdate':orderdate,'godowns':godowns})

def viewOrder(request,id):
    ogorder = get_object_or_404(ChemicalsAllOrders, id=id)
    try:
        recieved_recs=get_list_or_404(ColorRecord, order_no=ogorder.order_no,state="Godown",color = ogorder.color, unit = ogorder.unit)
    except:
        recieved_recs=[]
    # mindate=str(rec.order_date)
    d=datetime.date.today().strftime('%Y-%m-%d')
    # d=.recieving_date
    d=str(d)
    orderdate=str(ogorder.order_date)
    billdate=str(ogorder.bill_date)
    godowns = ChemicalsGodownsMaster.objects.all().order_by('godown')
    print(billdate)
    remaining_order = 0

    for r in recieved_recs:

        remaining_order = remaining_order + r.quantity
    remaining_order = ogorder.quantity - remaining_order
    return render(request, './ColorChemicalModule/vieworder.html', {'d':d,'billdate':billdate,'record':ogorder,'orderdate':orderdate,'godowns':godowns,'recieved_recs':recieved_recs,'remaining':remaining_order})

######################### validate order ##########################
def renderValidate(request,id):
    rec=get_object_or_404(ChemicalsAllOrders, id=id)
    mindate=str(rec.order_date)
    maxdate=datetime.date.today().strftime('%Y-%m-%d')


    return render(request, './ColorChemicalModule/validateorder.html', {'record':rec,'mindate':mindate,'maxdate':maxdate})

def validate(request,id):
    rec = get_object_or_404(ColorRecord,id=id)
    rec.bill_no=int(request.POST.get('billno'+str(rec.id)))
    rec.bill_date = request.POST.get('billdate'+str(rec.id))

    rec.save()
    all_recs = ColorRecord.objects.filter(order_no=rec.order_no,color=rec.color,unit=rec.unit).exclude(bill_date=None)
    q=0
    for i in all_recs:
        q=q+i.quantity
    ogorder=ChemicalsAllOrders.objects.filter(order_no=rec.order_no,color=rec.color,unit=rec.unit).first()
    if(q==ogorder.quantity):
        ogorder.validation="Yes"
        ogorder.save()

    messages.success(request,"Order Validated")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

#################### PLACED ORDERS TO GODOWN #######################
def goodsApprove(request,id):
    prevRec = get_object_or_404(ColorRecord,id=id)
    quantity_recieved = float(request.POST.get("quantityreceived"))
    g_id = int(request.POST.get('godownnumber'))
    godown=get_object_or_404(ChemicalsGodownsMaster,id=g_id)
    recieving_date = request.POST.get('receivingdate')
    recieve_date = datetime.datetime.strptime(recieving_date,'%Y-%m-%d').date()
    amount = prevRec.amount
    print(str(recieving_date))
    if(prevRec.quantity == quantity_recieved):
        prevRec.state="Godown"
        prevRec.recieving_date=str(recieving_date)
        prevRec.godown=godown
        prevRec.chalan_no=int(request.POST.get('chalan'))
        prevRec.recieving_date_string=str(recieving_date)
        prevRec.save()
        ogorder = get_object_or_404(ChemicalsAllOrders,order_no=prevRec.order_no,color=prevRec.color,unit=prevRec.unit)
        ogorder.state="Godown"
        ogorder.rem_quantity = 0
        ogorder.chalan_no=int(request.POST.get('chalan'))
        ogorder.save()
        try:


            try:
                try:
                    closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(godown=godown,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
                    closing_stock_pg.quantity=round(closing_stock_pg.quantity + quantity_recieved,2)
                    closing_stock_pg.save()

                except:
                    try:
                        closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(godown=godown,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                        pq=closing_stock_prev_pg.quantity
                    except:
                        pq=0
                    newpg= ChemicalsClosingStockperGodown(
                        color = get_object_or_404(Color,id=int(prevRec.color.id)),
                        quantity = round(pq + quantity_recieved,2),
                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                        rate = prevRec.rate,
                        dailydate = recieve_date,
                        godown=godown
                    )
                    newpg.save()
                #closing_stock = ClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit).order_by('-dailydate').first()
                closing_stock = ChemicalsClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()    ####loophole solved
                closing_stock.quantity=round(closing_stock.quantity + quantity_recieved,2)
                closing_stock.save()



            except:
                closing_stock_prev = ChemicalsClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()

                closing_stock= ChemicalsClosingStock(
                    color = get_object_or_404(Color,id=int(prevRec.color.id)),
                    quantity = round(closing_stock_prev.quantity + quantity_recieved,2),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                    rate = prevRec.rate,
                    dailydate = recieve_date
                )
                closing_stock.save()
            godown_color = get_object_or_404(ChemicalsGodownLooseMergeStock,color=prevRec.color,unit=prevRec.unit,state=godown)
            godown_color.quantity = round(godown_color.quantity + quantity_recieved,2)
            godown_color.rate = (godown_color.rate + prevRec.rate)/2
            godown_color.save()
        except:
            godown_color = ChemicalsGodownLooseMergeStock(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                state = godown
            )
            godown_color.save()
            closing_stock= ChemicalsClosingStock(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                dailydate = recieve_date
            )
            closing_stock.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/ordergeneration')
    elif(prevRec.quantity<quantity_recieved):
        messages.error(request,"Quantity Recieved cannot be more than Original Amount of Chemicals")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        quantity_remaining = round(prevRec.quantity - quantity_recieved)

        amount_per_quant = prevRec.amount/prevRec.quantity
        amount_recieved = amount_per_quant * quantity_recieved
        amount_remain = prevRec.amount - amount_recieved

        print(prevRec.color,prevRec.supplier,prevRec.unit,godown)
        color_ob=get_object_or_404(Color,id=int(prevRec.color.id))
        supp_ob=get_object_or_404(ColorAndChemicalsSupplier,id=int(prevRec.supplier.id))
        unit_ob=get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id))

        new_value = ColorRecord(
            recieving_date_string=str(recieving_date),
            recieving_date=str(recieving_date),
            color=color_ob,
            supplier=supp_ob,
            order_no=prevRec.order_no,
            order_date=prevRec.order_date,
            rate=prevRec.rate,
            amount=round(amount_recieved,2),
            quantity=quantity_recieved,
            unit = unit_ob,
            state="Godown",
            total_quantity = prevRec.total_quantity,
            godown = godown,
            chalan_no=int(request.POST.get('chalan')),


        )

        new_value.save()


        print(recieving_date)
        if quantity_recieved == 0 :
            messages.error(request,"Quantity Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:


            prevRec.quantity = round(prevRec.quantity - quantity_recieved,2)
            prevRec.amount = round(amount_remain,2)
            prevRec.save()
            ogorder = get_object_or_404(ChemicalsAllOrders,order_no=prevRec.order_no,color=prevRec.color,unit=prevRec.unit)
            ogorder.state="In Transit"
            ogorder.rem_quantity= round(ogorder.rem_quantity - quantity_recieved,2)
            ogorder.save()
            try:

                try:
                    try:
                        print("11")
                        closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(godown=godown,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
                        print("12")
                        closing_stock_pg.quantity=round(closing_stock_pg.quantity + quantity_recieved,2)
                        print("13")
                        closing_stock_pg.save()
                        print("14")

                    except:
                        try:
                            closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(godown=godown,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                            pq=closing_stock_prev_pg.quantity
                        except:
                            pq=0


                        newpg= ChemicalsClosingStockperGodown(
                            color = get_object_or_404(Color,id=int(prevRec.color.id)),
                            quantity = round(pq + quantity_recieved,2),
                            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                            rate = prevRec.rate,
                            dailydate = recieve_date,
                            godown=godown
                        )
                        newpg.save()
                    closing_stock = ChemicalsClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
                    closing_stock.quantity=round(closing_stock.quantity + quantity_recieved,2)
                    closing_stock.save()
                    print("same rec",closing_stock.quantity)
                except:
                    closing_stock_prev = ChemicalsClosingStock.objects.filter(color=prevRec.color,unit=prevRec.unit,dailydate__lt=recieve_date).order_by('-dailydate').first()

                    closing_stock= ChemicalsClosingStock(
                        color = get_object_or_404(Color,id=int(prevRec.color.id)),
                        quantity = round(closing_stock_prev.quantity + quantity_recieved,2),
                        unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                        rate = prevRec.rate,
                        dailydate = recieve_date
                    )
                    closing_stock.save()
                    print("exc")

                godown_color = get_object_or_404(ChemicalsGodownLooseMergeStock,color=prevRec.color,unit=prevRec.unit,state=godown)
                godown_color.quantity = round(godown_color.quantity + quantity_recieved,2)
                godown_color.rate = (godown_color.rate + prevRec.rate)/2
                godown_color.save()
                print("godown")
            except:
                godown_color = ChemicalsGodownLooseMergeStock(
                    color = get_object_or_404(Color,id=int(prevRec.color.id)),
                    quantity = round(quantity_recieved,2),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                    rate = prevRec.rate,
                    state = godown
                )
                godown_color.save()
                closing_stock= ChemicalsClosingStock(
                    color = get_object_or_404(Color,id=int(prevRec.color.id)),
                    quantity = round(quantity_recieved,2),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                    rate = prevRec.rate,
                    dailydate = recieve_date
                )
                closing_stock.save()

            messages.success(request,"Data Updated Successfully")


        #print(than_in_transit,than_in_godown)
        return redirect('/ordergeneration')


# def htmltoText(html):
#     h=html2text.HTML2Text()
#     h.ignore_links=True
#     return h.handle(html)

################# Chemical in loose Godown ##################
def goodsLease(request):
    lease=ChemicalsLooseGodownMaster.objects.all()
    lease_list=[]
    for g in lease:
        lease_list.append(g)
    godown_colors = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state__in=lease_list,state=None).exclude(quantity=0).order_by('color')
    # rec=ColorRecord.objects.filter(state='Godown').order_by('godown','color')
    records_filter = GodownLeaseFilter(request.GET,queryset=godown_colors)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)
    # html = render_to_string('./ColorChemicalModule/lease.html',{'filter':records_filter,'colors':records})
    # text = htmltoText(html)
    # print(text)
    chemicals=Color.objects.all().order_by('color')
    loose_godowns=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request,'./ColorChemicalModule/lease.html',{'filter':records_filter,'colors':records,'chemicals':chemicals,'loose_godowns':loose_godowns})

def leaseRequest(request):
    godowns=ChemicalsGodownsMaster.objects.all()
    godowns_list=[]
    for g in godowns:
        godowns_list.append(g.godown)
    godown_colors = ChemicalsGodownLooseMergeStock.objects.filter(state__in=godowns_list).exclude(quantity=0)
    # rec=ColorRecord.objects.filter(state='Godown').order_by('godown','color')
    records_filter = GodownLeaseFilter(request.GET,queryset=godown_colors)
    # return render(request,'./GreyModule/intransit.html',{'records':records_filter})

    paginator = Paginator(records_filter.qs,20)
    page = request.GET.get('page')
    records = paginator.get_page(page)

    return render(request,'./ColorChemicalModule/leaserequest.html',{'filter':records_filter,'colors':records})

def viewGood(request,id):
    rec=get_object_or_404(ChemicalsGodownLooseMergeStock, id=id)
    # mindate=str(rec.recieving_date)
    # maxdate=datetime.date.today().strftime('%Y-%m-%d')
    d=datetime.date.today()
    d=str(d)
    # recievedate=str(rec.recieving_date)
    lease = ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request, './ColorChemicalModule/leaseapprove.html', {'d':d,'record':rec,'lease':lease})


def leaseApprove(request,id):
    prevRec = get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)
    quantity_recieved = round(float(request.POST.get("quantitylease")),2)
    l_id = request.POST.get('leasenumber')
    loose_godown = get_object_or_404(ChemicalsLooseGodownMaster,id=int(l_id))
    recieve_date=datetime.datetime.strptime(request.POST.get('movingdate'),'%Y-%m-%d').date()
    if(prevRec.quantity == quantity_recieved):
        try:
            closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            print(closing_stock_g)
            closing_stock_g.quantity = round(closing_stock_g.quantity-quantity_recieved,2)
            print("sa")
            closing_stock_g.save()
        except:
            print("h1")
            closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
            print("h2")
            newpg= ChemicalsClosingStockperGodown(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(closing_stock_g.quantity -  quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                dailydate = recieve_date,
                godown=prevRec.state
            )
            newpg.save()
            print("h3")
        try:

            print("1")
            closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            print(closing_stock_pg)
            closing_stock_pg.quantity=round(closing_stock_pg.quantity + quantity_recieved,2)
            print("4")
            closing_stock_pg.save()
            print("5")

        except:
            print("here")
            # try:
            #     closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            #     closing_stock_g.quantity = round(closing_stock_g.quantity-quantity_recieved,2)
            #     closing_stock_g.save()
            # except:
            #     closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate_lt = recieve_date).order_by('-dailydate').first()
            #     newpg= ChemicalsClosingStockperGodown(
            #         color = get_object_or_404(Color,id=int(prevRec.color.id)),
            #         quantity = round(closing_stock_g.quantity -  quantity_recieved,2),
            #         unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
            #         rate = prevRec.rate,
            #         dailydate = recieve_date,
            #         godown=prevRec.state
            #     )
            #     newpg.save()
            try:
                closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                pq=closing_stock_prev_pg.quantity
            except:
                pq=0


            newpg= ChemicalsClosingStockperGodown(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(pq + quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                dailydate = recieve_date,
                loose_godown=loose_godown
                )
            newpg.save()
          ####################3
        try:
            godown_color = get_object_or_404(ChemicalsGodownLooseMergeStock,color=prevRec.color,unit=prevRec.unit,loose_godown_state=loose_godown)
            godown_color.quantity = round(godown_color.quantity + quantity_recieved,2)
            # r = round(((godown_color.rate + prevRec.rate)/2),2)
            # godown_color.rate=prevRec.rate
            godown_color.save()
        except:
            godown_color = ChemicalsGodownLooseMergeStock(
                color = prevRec.color,
                quantity = round(quantity_recieved,2),
                unit = prevRec.unit,
                rate = prevRec.rate,
                state = None,
                loose_godown_state=loose_godown
            )
            godown_color.save()
        prevRec.quantity=0
        prevRec.save()
        messages.success(request,"Data Updated Successfully")
        return redirect('/goodsreceived')
    elif(prevRec.quantity<quantity_recieved):
        messages.error(request,"Quantity Recieved cannot be more than Original Amount of Than")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        quantity_remaining = round(prevRec.quantity - quantity_recieved,2)
        try:
            try:
                print("21")
                closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
                print(closing_stock_g)
                closing_stock_g.quantity = round(closing_stock_g.quantity-quantity_recieved,2)
                print("23")
                closing_stock_g.save()
                print("24")
            except:
                closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                newpg= ChemicalsClosingStockperGodown(
                    color = get_object_or_404(Color,id=int(prevRec.color.id)),
                    quantity = round(closing_stock_g.quantity -  quantity_recieved,2),
                    unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                    rate = prevRec.rate,
                    dailydate = recieve_date,
                    godown=prevRec.state
                )
                newpg.save()
            closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            closing_stock_pg.quantity=round(closing_stock_pg.quantity + quantity_recieved,2)
            closing_stock_pg.save()


        except:
            # try:
            #     closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate = recieve_date).order_by('-dailydate').first()
            #     closing_stock_g.quantity = round(closing_stock_g.quantity-quantity_recieved,2)
            #     closing_stock_g.save()
            # except:
            #     closing_stock_g = ChemicalsClosingStockperGodown.objects.filter(godown=prevRec.state,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
            #     newpg= ChemicalsClosingStockperGodown(
            #         color = get_object_or_404(Color,id=int(prevRec.color.id)),
            #         quantity = round(closing_stock_g.quantity -  quantity_recieved,2),
            #         unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
            #         rate = prevRec.rate,
            #         dailydate = recieve_date,
            #         godown=prevRec.state
            #     )
            #     newpg.save()
            try:
                closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown,color=prevRec.color,unit=prevRec.unit,dailydate__lt = recieve_date).order_by('-dailydate').first()
                pq=closing_stock_prev_pg.quantity
            except:
                pq=0


            newpg= ChemicalsClosingStockperGodown(
                color = get_object_or_404(Color,id=int(prevRec.color.id)),
                quantity = round(pq + quantity_recieved,2),
                unit = get_object_or_404(ChemicalsUnitsMaster,id=int(prevRec.unit.id)),
                rate = prevRec.rate,
                dailydate = recieve_date,
                loose_godown=loose_godown
                )
            newpg.save()
        try:
            godown_color = get_object_or_404(ChemicalsGodownLooseMergeStock,color=prevRec.color,unit=prevRec.unit,loose_godown_state=loose_godown)
            godown_color.quantity = round(godown_color.quantity + quantity_recieved,2)
            # godown_color.rate = prevRec.rate

        except:
            godown_color = ChemicalsGodownLooseMergeStock(
                color = prevRec.color,
                quantity = round(quantity_recieved,2),
                unit = prevRec.unit,
                rate = prevRec.rate,
                state = None,
                loose_godown_state=loose_godown
            )

        if quantity_recieved == 0 :
            messages.error(request,"Quantity Recieved cannot be Zero (0)")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            prevRec.quantity=quantity_remaining
            prevRec.save()
            godown_color.save()
            messages.success(request,"Data Updated Successfully")


    return redirect('/goodsreceived')

def changeLooseGodown(request,id):
    leasestock = get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)
    #color = Color.objects.all().order_by('color')
    #units=ChemicalsUnitsMaster.objects.all().order_by('unit')
    #godowns=ChemicalsGodownsMaster.objects.all().order_by('godown')
    loose_godown=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request,'./ColorChemicalModule/editloosestocklg.html',{'record':leasestock,'loose':loose_godown})

def savechangeLooseGodown(request,id):
    if(float(request.POST.get('move-quantity'))==0):
        messages.error(request,"Please enter valid quantity")
        return redirect('/goodslease')
    l_id=request.POST.get('loosename')
    loose_object=get_object_or_404(ChemicalsLooseGodownMaster,id=int(l_id))
    move_quantity=round(float(request.POST.get('move-quantity')),2)

    merge_stock=get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)
    if(loose_object==merge_stock.loose_godown_state):
        messages.error(request,"Cannot update because loose godown you selected is same as previous")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    try:
        merge_stock_other=get_object_or_404(ChemicalsGodownLooseMergeStock,loose_godown_state=loose_object,color=merge_stock.color,unit=merge_stock.unit)
        merge_stock_other.quantity=round(merge_stock_other.quantity+move_quantity,2)
        merge_stock_other.save()
    except:
        new_merge_stock_other=ChemicalsGodownLooseMergeStock(
            color=merge_stock.color,
            unit=merge_stock.unit,
            quantity=move_quantity,
            rate=merge_stock.rate,
            state=None,
            loose_godown_state=loose_object
        )
        new_merge_stock_other.save()
    merge_stock.quantity=round(merge_stock.quantity - move_quantity)
    merge_stock.save()


    prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=merge_stock.loose_godown_state,color=merge_stock.color,unit=merge_stock.unit).order_by('-dailydate').first()
    prevlg.quantity = round(prevlg.quantity - move_quantity,2)
    prevlg.save()
    try:

        print("1")
        closing_stock_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_object,color=merge_stock.color,unit=merge_stock.unit,dailydate=prevlg.dailydate).order_by('-dailydate').first()
        print(closing_stock_pg)
        closing_stock_pg.quantity=round(closing_stock_pg.quantity + move_quantity,2)
        print("4")
        closing_stock_pg.save()
        print("5")

    except:
        print("here")

        try:
            closing_stock_prev_pg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_object,color=merge_stock.color,unit=merge_stock.unit,dailydate__lt = prevlg.dailydate).order_by('-dailydate').first()
            pq=closing_stock_prev_pg.quantity
        except:
            pq=0


        newpg= ChemicalsClosingStockperGodown(
            color = get_object_or_404(Color,id=int(merge_stock.color.id)),
            quantity = round(pq + move_quantity,2),
            unit = get_object_or_404(ChemicalsUnitsMaster,id=int(merge_stock.unit.id)),
            rate = merge_stock.rate,
            dailydate = prevlg.dailydate,
            loose_godown=loose_object
            )
        newpg.save()



    messages.success(request,"Loose godown name changed")
    return redirect('/goodslease')

def leaseedit(request,id):
    leasestock = get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)
    color = Color.objects.all().order_by('color')
    units=ChemicalsUnitsMaster.objects.all().order_by('unit')
    godowns=ChemicalsGodownsMaster.objects.all().order_by('godown')
    loose_godown=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request,'./ColorChemicalModule/editloosestock.html',{'record':leasestock,'color':color,'units':units,'loose':loose_godown,'godowns':godowns})

def savelease(request,id):
    g_id=request.POST.get('godownname')
    godown_object=get_object_or_404(ChemicalsGodownsMaster,id=int(g_id))
    act_quantity=round(float(request.POST.get('act-quantity')),2)

    stock=get_object_or_404(ChemicalsGodownLooseMergeStock,id=id)

    old_quantity=stock.quantity
    diff=old_quantity-act_quantity
    if(diff<0):
        messages.error(request,"Please move extra quantity from godown section")
        return redirect('/goodsreceived')
    else:
        try:
            stockgodown=get_object_or_404(ChemicalsGodownLooseMergeStock,color=stock.color,unit=stock.unit,state=godown_object)
        except:
            messages.error(request,"Selected Godown never consisted this chemical")
            return redirect('/goodslease')
        stock.quantity=act_quantity
        stock.save()
        stockgodown.quantity=round(stockgodown.quantity+diff,2)
        stockgodown.save()

    prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=stock.loose_godown_state,color=stock.color,unit=stock.unit).order_by('-dailydate').first()
    prevlg.quantity = round(prevlg.quantity - diff,2)
    prevlg.save()

    prevgodown1 = ChemicalsClosingStockperGodown.objects.filter(godown=godown_object,color=stock.color,unit=stock.unit).order_by('-dailydate').first()
    prevgodown1.quantity = round(prevgodown1.quantity + diff)
    prevgodown1.save()

    messages.success(request,"Loose Godown quantity edited")
    return redirect('/goodslease')
########################### COLOR CHEMICAL LOOSE END ################################

########################### COLOR CHEMICAL DAILY CONSUMPTION ################################
def renderDailyConsumptionLease1(request):
    lease = ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    first_lease = ChemicalsLooseGodownMaster.objects.all().order_by('lease').first()
    try:
        color = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=first_lease.id).exclude(quantity=0).order_by('color')
    except:
        new_value = ChemicalsLooseGodownMaster(lease="Loose Godown 1")
        new_value.save()
        color = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=new_value.id).exclude(quantity=0).order_by('color')
    todays = ChemicalsDailyConsumption.objects.filter(con_date=str(datetime.date.today()))
    todaydate=str(datetime.date.today())
    return render(request,'./ColorChemicalModule/dailyconsumption.html',{'colors':color,'today':todaydate,'lease':lease,'name':first_lease.lease})

def renderDailyConsumptionLease2(request):
    l_id= request.POST.get('lease')
    loose_godown_object = get_object_or_404(ChemicalsLooseGodownMaster,id=int(l_id))
    leases = ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    color = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=loose_godown_object).exclude(quantity=0).order_by('color')
    todays = ChemicalsDailyConsumption.objects.filter(con_date=str(datetime.date.today()))
    todaydate=str(datetime.date.today())
    return render(request,'./ColorChemicalModule/dailyconsumption.html',{'colors':color,'today':todaydate,'lease':leases,'name':loose_godown_object.lease})

def backToDailyConsumption(request):
    return redirect('/dailyconsumptiondetails')

def dailyconsumptionDetails(request):
    l=ChemicalsLooseGodownMaster.objects.all().first()
    todays = ChemicalsDailyConsumption.objects.filter(con_date=str(datetime.date.today()),loose_godown=l).exclude(quantity=0)
    return render(request,'./ColorChemicalModule/dailyconsumptiondetails.html',{'records':todays,'d':str(datetime.date.today()),'date':str(datetime.date.today())})

def dailyconsumptionDetails2(request):
    date_c=request.POST.get('consumingdate')
    # date_c=datetime.datetime.strptime(date_c,"%Y-%m-%d").date()
    todays = ChemicalsDailyConsumption.objects.filter(con_date=date_c).exclude(quantity=0)
    return render(request,'./ColorChemicalModule/dailyconsumptiondetails.html',{'records':todays,'d':str(datetime.date.today()),'date':date_c})

def editDailyConsumption(request,id):
    rec=get_object_or_404(ChemicalsDailyConsumption,id=id)
    d=str(rec.con_date)
    return render(request,'./ColorChemicalModule/editdailyconsumption.html',{'record':rec,'d':d})

def saveDailyConsumption(request,id):
    rec=get_object_or_404(ChemicalsDailyConsumption,id=id)
    new_q=float(request.POST.get('new-quantity'))


    if(new_q>rec.quantity):
        messages.error(request,"Quantity cannot exceed original quantity")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    elif(new_q==rec.quantity):
        messages.error(request,"Quantity is same as original quantity")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    begin=datetime.datetime.strptime(str(rec.con_date),"%Y-%m-%d").date()
    end=datetime.date.today()
    selected_dates=[]

    # selected_qualities=[]
    next_day = begin
    while True:
        if next_day > end:
            break
        selected_dates.append((datetime.datetime.strptime(str(next_day), '%Y-%m-%d')))#.strftime('%b %d,%Y'))
        next_day += datetime.timedelta(days=1)

    #loose_godown_object=get_object_or_404(ChemicalsLooseGodownMaster,lease=rec.loose_godown.lease)
    #colors = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=loose_godown_object,).order_by('color')
    merge_color=get_object_or_404(ChemicalsGodownLooseMergeStock,color=rec.color,unit=rec.unit,loose_godown_state=rec.loose_godown)
    merge_color.quantity=round((merge_color.quantity + rec.quantity - new_q),2)
    merge_color.save()

    try:
        all_closingstocks=ChemicalsClosingStock.objects.filter(color=rec.color,unit=rec.unit,dailydate__in=selected_dates)

        for a in all_closingstocks:
            a.quantity=round((a.quantity + rec.quantity - new_q),2)
            a.save()


    except:
        pass

    try:
        all_prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=rec.loose_godown,color=rec.color,unit=rec.unit,dailydate__in=selected_dates).order_by('dailydate')

        for a in all_prevlg:

            a.quantity=round((a.quantity + rec.quantity - new_q),2)
            a.save()
    except:
        pass
    rec.quantity_remaining=round((rec.quantity_remaining+rec.quantity-new_q),2)
    rec.quantity=new_q

    rec.save()
    return redirect('/dailyconsumptiondetails')

######################## CONSUME STOCK FROM LOOSE GODOWN ######################
def consume(request,name):
    loose_godown_object=get_object_or_404(ChemicalsLooseGodownMaster,lease=name)
    colors = ChemicalsGodownLooseMergeStock.objects.filter(loose_godown_state=loose_godown_object).exclude(quantity=0).order_by('color')
    flag = 0
    consumingdate=request.POST.get('consumingdate')
    # print(consumingdate)
    # print(str(consumingdate))
    begin=datetime.datetime.strptime(consumingdate,"%Y-%m-%d").date()
    end=datetime.date.today()
    selected_dates=[]

    # selected_qualities=[]
    next_day = begin
    while True:
        if next_day > end:
            break
        selected_dates.append((datetime.datetime.strptime(str(next_day), '%Y-%m-%d')))#.strftime('%b %d,%Y'))
        next_day += datetime.timedelta(days=1)

    print(selected_dates)
    for c in colors:
        if(request.POST.get(str(c.id))==""):

            continue
        if(float(request.POST.get(str(c.id)))>c.quantity):
            flag = flag + 1
            continue

        try:
            prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown_object,color=c.color,unit=c.unit,dailydate__lte=str(consumingdate)).order_by('-dailydate').first()


            if(str(datetime.date.today()) != consumingdate):
                print("diff")
                all_prevlg = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown_object,color=c.color,unit=c.unit,dailydate__in=selected_dates).order_by('dailydate')

                for a in all_prevlg:
                    print("d")
                    a.quantity=round(a.quantity - float(request.POST.get(str(c.id))),2)
                    a.save()
                recbefore = ChemicalsClosingStockperGodown.objects.filter(loose_godown=loose_godown_object,color=c.color,unit=c.unit,dailydate__in=selected_dates).order_by('-dailydate').first()
                if(str(datetime.date.today()) != str(recbefore.dailydate)):
                    new_lg = ChemicalsClosingStockperGodown(
                        color=c.color,
                        unit=c.unit,
                        quantity=recbefore.quantity,
                        dailydate=str(datetime.date.today()),
                        rate=c.rate,
                        loose_godown = loose_godown_object
                    )
                    new_lg.save()
            else:
                if(str(prevlg.dailydate)!=str(datetime.date.today())):
                    new_lg = ChemicalsClosingStockperGodown(
                        color=c.color,
                        unit=c.unit,
                        quantity=round((prevlg.quantity - float(request.POST.get(str(c.id)))),2),
                        dailydate=str(datetime.date.today()),
                        rate=c.rate,
                        loose_godown = loose_godown_object
                    )
                    new_lg.save()
                else:
                    prevlg.quantity = round(prevlg.quantity - float(request.POST.get(str(c.id))),2)
                    prevlg.save()

        except:
            pass
        try:
            closing_stock = ChemicalsClosingStock.objects.filter(color=c.color,unit=c.unit,dailydate__lte=str(consumingdate)).order_by('-dailydate').first()
            print(str(closing_stock.dailydate),closing_stock.quantity,type(closing_stock.dailydate))
            print(type(consumingdate))
            #closing_stock = ClosingStock.objects.filter(color=c.color,unit=c.unit).order_by('-dailydate').first()
            if(str(closing_stock.dailydate) != consumingdate):
                print("done4")
                new_cs = ChemicalsClosingStock(
                    color=c.color,
                    unit=c.unit,
                    quantity=round((closing_stock.quantity - float(request.POST.get(str(c.id)))),2),
                    dailydate=str(consumingdate),
                    rate=c.rate
                )
                new_cs.save()
            else:
                closing_stock.quantity=round((closing_stock.quantity - float(request.POST.get(str(c.id)))),2)
                closing_stock.save()
                print("done")
            new_dates=selected_dates[1:]


            all_closingstocks = ChemicalsClosingStock.objects.filter(color=c.color,unit=c.unit,dailydate__in=new_dates)
            #print("got all")
            #print(new_dates)
            for a in all_closingstocks:
                print(a.color)
                print(a.dailydate)
                a.quantity=round((a.quantity-float(request.POST.get(str(c.id)))),2)
                a.save()
        except:
            #print("ec")
            pass



        c.quantity=round((c.quantity - float(request.POST.get(str(c.id)))),2)
        c.save()
        stored_color = ChemicalsGodownLooseMergeStock.objects.filter(color=c.color,unit=c.unit)
        q=0
        for sc in stored_color:
            q=round((q+sc.quantity),2)

        daily_consump = ChemicalsDailyConsumption(
            con_date = str(consumingdate),
            color = c.color,
            unit = c.unit,
            quantity = round(float(request.POST.get(str(c.id))),2),
            quantity_remaining = q,
            loose_godown= loose_godown_object
        )
        daily_consump.save()

    if (flag != 0):
        messages.error(request,"%s Quantity entered exceeded the quantities available in Loose" %(flag))
    return redirect('/dailyconsumption1')


########################### DISPLAY CLOSING STOCK #############################
def renderClosingStock(request):
    godowns=ChemicalsGodownsMaster.objects.all()
    godowns_list=[]
    for g in godowns:
        godowns_list.append(g)

    lease=ChemicalsLooseGodownMaster.objects.all()
    lease_list=[]
    for l in lease:
        lease_list.append(l)

    datalist=[]
    colors=Color.objects.all()
    units=ChemicalsUnitsMaster.objects.all()
    for c in colors:
        for u in units:
            try:
                lq=0
                recsl=get_list_or_404(ChemicalsGodownLooseMergeStock,color=c,unit=u,loose_godown_state__in=lease_list)
                for i in recsl:
                    lq=lq+i.quantity

                recsg=get_list_or_404(ChemicalsGodownLooseMergeStock,color=c,unit=u,state__in=godowns_list,loose_godown_state=None)
                lg=0
                for i in recsg:
                    lg=lg+i.quantity
                l=[]
                l.append(c.color)
                l.append(u.unit)
                l.append(lq)
                l.append(lg)
                l.append(round(lq+lg,2))
                datalist.append(l)
            except:
                try:
                    recsg=get_list_or_404(ChemicalsGodownLooseMergeStock,color=c,unit=u,state__in=godowns_list,loose_godown_state=None)

                    lg=0
                    for i in recsg:
                        lg=lg+i.quantity
                    l=[]
                    l.append(c.color)
                    l.append(u.unit)
                    l.append(0)
                    l.append(lg)
                    l.append(lg)
                    datalist.append(l)

                except:
                    pass


    return render(request,'./ColorChemicalModule/closingstock.html',{'colors':datalist})

########################### COLOR REPORT FILTER #################################
def renderColorReportFilter(request):
    d=str(datetime.date.today())
    godowns = ChemicalsGodownsMaster.objects.all().order_by('godown')
    loose_godowns=ChemicalsLooseGodownMaster.objects.all().order_by('lease')
    return render(request,'./ColorChemicalModule/reportFilter.html',{'d':d,'godowns':godowns,'loose':loose_godowns})

# def colorReport(request):
#     begin = request.POST.get("start_date")
#     end = request.POST.get("end_date")
#     if(begin!="" or end!=""):

#         begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
#         end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
#         selected_dates=[]

#     # selected_qualities=[]
#         next_day = begin
#         while True:
#             if next_day > end:
#                 break



#             selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
#             next_day += datetime.timedelta(days=1)
#     datalist=[]
#     colors= Color.objects.all()
#     units= Units.objects.all()
#     for c in colors:
#         for u in units:
#             try:
#                 records=get_list_or_404(DailyConsumption,con_date__in=selected_dates,color=c.color,unit=u.unit)
#                 l=[]
#                 quantity = 0
#                 for rec in records:
#                     quantity = quantity+rec.quantity
#                 l.append(c.color)
#                 l.append(u.unit)

#                 try:
#                     first_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[0],color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 except:
#                     first_record = ClosingStock.objects.filter(color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 try:
#                     last_record = get_object_or_404(ClosingStock,dailydate=selected_dates[-1],color = c.color,unit = u.unit)
#                 except:
#                     last_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[-1],color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 l.append(first_record.quantity)
#                 l.append(quantity)
#                 l.append(last_record.quantity)
#                 datalist.append(l)
#                 print(first_record.quantity,first_record.con_date)
#             except:
#                 l=[]
#                 l.append(c.color)
#                 l.append(u.unit)

#                 try:
#                     first_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[0],color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 except:
#                     first_record = ClosingStock.objects.filter(color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 try:
#                     last_record = get_object_or_404(ClosingStock,dailydate=selected_dates[-1],color = c.color,unit = u.unit)
#                 except:
#                     last_record = ClosingStock.objects.filter(dailydate__lt=selected_dates[-1],color = c.color,unit = u.unit).order_by('-dailydate').first()
#                 l.append(0)
#                 l.append(0)
#                 l.append(0)
#                 datalist.append(l)

#     return render(request,'./ColorChemicalModule/report.html',{'data':datalist,'begin':begin,'end':end})


########### previous working color report

# def colorReport(request):
#     begin = request.POST.get("start_date")
#     end = request.POST.get("end_date")
#     if(begin!="" or end!=""):

#         begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
#         end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
#         selected_dates=[]

#     # selected_qualities=[]
#         next_day = begin
#         while True:
#             if next_day > end:
#                 break



#             selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
#             next_day += datetime.timedelta(days=1)
#     datalist=[]
#     colors= Color.objects.all()
#     units= ChemicalsUnitsMaster.objects.all()
#     for c in colors:
#         for u in units:
#             try:
#                 l=[]
#                 try:
#                     first_record = ChemicalsClosingStock.objects.filter(dailydate__lt=selected_dates[0],color = c,unit = u).order_by('-dailydate').first()
#                     l.append(c.color)
#                     l.append(u.unit)
#                     l.append(first_record.quantity)
#                 except:

#                     l.append(0)
#                 try:
#                     last_record = get_object_or_404(ChemicalsClosingStock,dailydate=selected_dates[-1],color = c,unit = u)
#                 except:
#                     last_record = ChemicalsClosingStock.objects.filter(dailydate__lt=selected_dates[-1],color = c,unit = u).order_by('-dailydate').first()


#                 try:
#                     records=get_list_or_404(ChemicalsDailyConsumption,con_date__in=selected_dates,color=c,unit=u)


#                     quantity = 0
#                     for rec in records:
#                         quantity = quantity+rec.quantity

#                     l.append(quantity)
#                 except:
#                     l.append(0)

#                 l.append(last_record.quantity)
#                 new_stock=0
#                 try:

#                     #neworders = get_list_or_404(ColorRecord,recieving_date__in=selected_dates,color=c,unit=u)
#                     neworders=ColorRecord.objects.filter(recieving_date__in=selected_dates,color=c,unit=u)
#                     print(neworders)
#                     for i in neworders:

#                         new_stock=new_stock+i.quantity

#                 except:
#                     pass

#                 l.append(new_stock)
#                 datalist.append(l)
#                 # print(first_record.quantity,first_record.con_date)
#             except:
#                 pass
#     begin=str(begin)
#     end=str(end)
#     display_begin=datetime.datetime.strptime(str(begin),"%Y-%m-%d").date().strftime("%d/%m/%Y")
#     display_end=datetime.datetime.strptime(str(end),"%Y-%m-%d").date().strftime("%d/%m/%Y")
#     return render(request,'./ColorChemicalModule/report.html',{'data':datalist,'begin':begin,'end':end, 'display_begin': display_begin, 'display_end': display_end})

########################### COLOR REPORT MAIN FUNCTION #################################
def colorReport(request):
    begin = request.POST.get("start_date")
    end = request.POST.get("end_date")
    if(begin!="" or end!=""):

        begin=datetime.datetime.strptime(begin,"%Y-%m-%d").date()
        end=datetime.datetime.strptime(end,"%Y-%m-%d").date()
        selected_dates=[]

    # selected_qualities=[]
        next_day = begin
        while True:
            if next_day > end:
                break



            selected_dates.append(datetime.datetime.strptime(str(next_day), '%Y-%m-%d'))#.strftime('%b %d,%Y'))
            next_day += datetime.timedelta(days=1)
    datalist=[]
    colors= Color.objects.all()
    units= ChemicalsUnitsMaster.objects.all()

    godowns = ChemicalsGodownsMaster.objects.all().order_by('godown')
    loose_godowns=ChemicalsLooseGodownMaster.objects.all().order_by('lease')

    selected_godowns=[]
    selected_loose=[]
    selected_godowns_id=[]
    selected_loose_id=[]
    for g in godowns:
        if(request.POST.get(g.godown)!=None):
            selected_godowns.append(get_object_or_404(ChemicalsGodownsMaster,id=int(request.POST.get(g.godown))))
            selected_godowns_id.append(int(request.POST.get(g.godown)))
    for g in loose_godowns:
        if(request.POST.get(g.lease)!=None):
            selected_loose.append(get_object_or_404(ChemicalsLooseGodownMaster,id=int(request.POST.get(g.lease))))
            selected_loose_id.append(int(request.POST.get(g.lease)))

    if selected_loose==[] and selected_godowns == []:
        for g in loose_godowns:
            selected_loose.append(g)
        for g in godowns:
            selected_godowns.append(g)

    # if selected_godowns == []:
    #     for g in godowns:
    #         selected_godowns.append(g)

    for c in colors:
        for u in units:
            try:
                l=[]

    ######################### opening stock ##################################
                try:
                    l.append(c.color)
                    l.append(u.unit)
                    quan=0
                    for g in selected_godowns:
                        first_record = ChemicalsClosingStockperGodown.objects.filter(dailydate__lt=selected_dates[0],color = c,unit = u,godown=g).order_by('-dailydate').first()
                        try:
                            quan=quan+first_record.quantity
                        except:
                            pass

                    for lg in selected_loose:
                        first_record = ChemicalsClosingStockperGodown.objects.filter(dailydate__lt=selected_dates[0],color = c,unit = u,loose_godown=lg).order_by('-dailydate').first()
                        try:
                            quan=quan+first_record.quantity
                        except:
                            pass

                    l.append(quan)
                except:

                    l.append(0)

###################### new stock #################################
                new_stock=0
                if selected_loose==[] and selected_godowns!=[]:
                    try:

                        #neworders = get_list_or_404(ColorRecord,recieving_date__in=selected_dates,color=c,unit=u)
                        neworders=ColorRecord.objects.filter(recieving_date__in=selected_dates,color=c,unit=u,godown__in=selected_godowns)

                        for i in neworders:

                            new_stock=new_stock+i.quantity

                    except:
                        pass
                elif selected_godowns==[] and selected_loose!=[]:
                    try:
                        records=get_list_or_404(ChemicalsDailyConsumption,con_date__in=selected_dates,color=c,unit=u,loose_godown__in=selected_loose)


                        quantity = 0
                        for rec in records:
                            quantity = quantity+rec.quantity

                        consumed_stock=quantity

                    except:
                        consumed_stock=0
                    try:
                        q=0
                        for lg in selected_loose:
                            lstock = ChemicalsClosingStockperGodown.objects.filter(dailydate__lte=selected_dates[-1],color = c,unit = u,loose_godown=lg).order_by('-dailydate').first()
                            fstock = ChemicalsClosingStockperGodown.objects.filter(dailydate__lt=selected_dates[0],color = c,unit = u,loose_godown=lg).order_by('-dailydate').first()
                            print(fstock)
                            if fstock:

                                q= q+lstock.quantity - fstock.quantity
                            else:
                                q=q+lstock.quantity

                        new_stock=q+consumed_stock
                    except:
                        pass


                else:
                    try:

                        #neworders = get_list_or_404(ColorRecord,recieving_date__in=selected_dates,color=c,unit=u)
                        neworders=ColorRecord.objects.filter(recieving_date__in=selected_dates,color=c,unit=u,godown__in=selected_godowns)

                        for i in neworders:

                            new_stock=new_stock+i.quantity

                    except:
                        pass
                l.append(new_stock)

################################# consumption ########################################
                if selected_godowns!=[] and selected_loose==[]:
                    l.append("loop")
                elif selected_loose!=[] and selected_godowns==[]:
                    try:
                        records=get_list_or_404(ChemicalsDailyConsumption,con_date__in=selected_dates,color=c,unit=u,loose_godown__in=selected_loose)


                        quantity = 0
                        for rec in records:
                            quantity = quantity+rec.quantity

                        l.append(quantity)
                    except:
                        l.append(0)
                else:
                    try:
                        records=get_list_or_404(ChemicalsDailyConsumption,con_date__in=selected_dates,color=c,unit=u,loose_godown__in=selected_loose)


                        quantity = 0
                        for rec in records:
                            quantity = quantity+rec.quantity

                        l.append(quantity)
                    except:
                        l.append(0)
############################### closing stock ##############################
                try:
                    lquan=0
                    for g in selected_godowns:
                        last_record = ChemicalsClosingStockperGodown.objects.filter(dailydate__lte=selected_dates[-1],color = c,unit = u,godown=g).order_by('-dailydate').first()
                        try:
                            lquan=lquan+last_record.quantity
                        except:
                            pass
                    for s in selected_loose:
                        last_record1 = ChemicalsClosingStockperGodown.objects.filter(dailydate__lte=selected_dates[-1],color = c,unit = u,loose_godown=s).order_by('-dailydate').first()
                        try:
                            lquan=lquan+last_record1.quantity
                        except:
                            pass
                except:
                    pass


                l.append(lquan)

                if l[2]==0 and l[3]==0 and l[5]==0:
                    pass
                else:
                    datalist.append(l)
                # print(first_record.quantity,first_record.con_date)
            except:
                pass
    begin=str(begin)
    end=str(end)
    display_begin=datetime.datetime.strptime(str(begin),"%Y-%m-%d").date().strftime("%d/%m/%Y")
    display_end=datetime.datetime.strptime(str(end),"%Y-%m-%d").date().strftime("%d/%m/%Y")
    return render(request,'./ColorChemicalModule/report.html',{'data':datalist,'begin':begin,'end':end, 'display_begin': display_begin, 'display_end': display_end,'selected_godowns_id':selected_godowns_id,'selected_loose_id':selected_loose_id})

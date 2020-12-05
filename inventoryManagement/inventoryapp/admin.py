from django.contrib import admin
from .models import Record,Quality,Checker,ThanRange,ProcessingPartyName,ArrivalLocation,ColorSupplier,Color,ColorRecord,DailyConsumption,AllOrders,GodownLeaseColors,Godowns,Lease,Units,ClosingStock
from .models import Employee,MonthlyPayment,CompanyAccounts,Transport,CityMaster
from import_export.admin import ImportExportModelAdmin
# Register your models here.

@admin.register(Employee,MonthlyPayment,CityMaster,CompanyAccounts,Transport,Record,Quality,Checker,ThanRange,ProcessingPartyName,ArrivalLocation,ColorSupplier,Color,ColorRecord,DailyConsumption,AllOrders,GodownLeaseColors,Godowns,Lease,Units,ClosingStock)

class ItemAdmin(ImportExportModelAdmin):
    pass
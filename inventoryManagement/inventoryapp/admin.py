from django.contrib import admin
from .models import Record,GreyQualityMaster,GreyCheckerMaster,GreyCutRange,ProcessingPartyNameMaster,GreyArrivalLocationMaster,ColorSupplier,Color,ColorRecord,DailyConsumption,AllOrders,GodownLeaseColors,Godowns,Lease,Units,ClosingStock
from .models import Employee,MonthlyPayment,CompanyAccounts,GreyTransportMaster,CityMaster
from import_export.admin import ImportExportModelAdmin
# Register your models here.

@admin.register(Employee,MonthlyPayment,CityMaster,CompanyAccounts,GreyTransportMaster,Record,GreyQualityMaster,GreyCheckerMaster,GreyCutRange,ProcessingPartyNameMaster,GreyArrivalLocationMaster,ColorSupplier,Color,ColorRecord,DailyConsumption,AllOrders,GodownLeaseColors,Godowns,Lease,Units,ClosingStock)

class ItemAdmin(ImportExportModelAdmin):
    pass
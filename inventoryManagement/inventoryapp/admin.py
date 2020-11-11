from django.contrib import admin
from .models import Record,Quality,ProcessingPartyName,ArrivalLocation,ColorSupplier,Color,ColorRecord,DailyConsumption
from import_export.admin import ImportExportModelAdmin
# Register your models here.

@admin.register(Record,Quality,ProcessingPartyName,ArrivalLocation,ColorSupplier,Color,ColorRecord,DailyConsumption)

class ItemAdmin(ImportExportModelAdmin):
    pass
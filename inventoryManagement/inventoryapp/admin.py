from django.contrib import admin
from .models import Record,Quality,ProcessingPartyName,ArrivalLocation
from import_export.admin import ImportExportModelAdmin
# Register your models here.

@admin.register(Record,Quality,ProcessingPartyName,ArrivalLocation)

class ItemAdmin(ImportExportModelAdmin):
    pass
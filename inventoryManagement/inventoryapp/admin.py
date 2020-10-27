from django.contrib import admin
from .models import Record,Quality,ProcessingPartyName
from import_export.admin import ImportExportModelAdmin
# Register your models here.

@admin.register(Record,Quality,ProcessingPartyName)

class ItemAdmin(ImportExportModelAdmin):
    pass
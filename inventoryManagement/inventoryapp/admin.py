from django.contrib import admin
from .models import Record,Quality,Trial
from import_export.admin import ImportExportModelAdmin
# Register your models here.

@admin.register(Record,Quality,Trial)

class ItemAdmin(ImportExportModelAdmin):
    pass
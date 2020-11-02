from django.contrib import admin
from django.urls import path
from . import views

from django.conf.urls import (
    handler400,
    handler403,
    handler404, 
    handler500,
)

handler400 = 'inventoryapp.views.bad_request'
handler403 = 'inventoryapp.views.permission_denied'
handler404 = 'inventoryapp.views.page_not_found'
handler500 = 'inventoryapp.views.server_error'


urlpatterns = [
    path('index', views.index,name='index'),
    path('insert', views.upload,name='insert'),
    path('intransit',views.showIntransit, name='intransit'),
    path('record/<int:id>',views.record, name='record'),
    path('godown',views.showGodown, name='godown'),
    path('godownrequest',views.showGodownRequest, name='godownrequest'),
    path('godownapprove/<int:id>',views.goDownApprove, name='godownapprove'),
    path('item/<int:id>',views.edit, name="edit"),
    path('nextitem/<int:id>', views.nextRec, name='nextRec'),
    path('previtem/<int:id>', views.prevRec, name='prevRec'),
    path('approve/<int:id>',views.approveBale, name="approvebale"),
    path('checking', views.showChecked, name="checking"),
    path('checkingrequest',views.showCheckingRequest, name= "checkingrequest"),
    path('checkingapprove/<int:id>',views.checkingApprove, name='checkingapprove'),
    path('approvecheck/<int:id>',views.approveCheck, name="approvecheck"),
    path('editchecked/<int:id>',views.editChecked, name="editchecked"),
    path('checkededit/<int:id>',views.checkedEdit, name="checkededit"),
    path('addquality',views.renderAddQuality, name="addquality"),
    path('savequality',views.saveQuality, name="savequality"),
    path('addparty',views.renderAddParty, name="addparty"),
    path('saveparty',views.saveParty, name="saveparty"),
    path('inprocess',views.showProcessing, name='inprocess'),
    path('processingrequest',views.showProcessingRequest, name= "processingrequest"),
    path('processingapprove/<int:id>',views.processingApprove, name='processingapprove'),
    path('sendinprocess/<int:id>',views.sendInProcess, name="sendinprocess"),

    path('readytoprint',views.showReadyToPrint, name='readytoprint'),
    path('readytoprintrequest',views.showReadyRequest, name= "readytoprintrequest"),
    path('readyapprove/<int:id>',views.readyApprove, name='readyapprove'),
    path('sendreadytoprint/<int:id>',views.readyToPrint, name="sendreadytoprint"),
    path('back',views.back1,name="back1"),
    path('back2',views.back2checking,name="back2checking"),
    path('back/<str:state>',views.back,name="back"),

    path('deleteparty/<int:id>',views.deleteProcessingParty,name="deleteprocessingparty"),
    path('editparty/<int:id>',views.renderEditParty,name="rendereditparty"),
    path('editprocessingparty/<int:id>',views.editProcessingParty,name="editprocessingparty"),
    path('deletequality/<int:id>',views.deleteQuality,name="deletequality"),
    path('editquality/<int:id>',views.renderEditQuality,name="rendereditquality"),
    path('editgreyquality/<int:id>',views.editQuality,name="editquality"),

    path('reportfilter',views.reportFilter, name='reportfilter'),
    path('report',views.generateReport,name='generatereport'),
    path('showdefective',views.showDefective,name='showdefective'),

    path('qualityreportfilter',views.qualityReportFilter, name='qualityreportfilter'),
    path('qualityreport',views.qualityReport,name='qualityreport'),
]
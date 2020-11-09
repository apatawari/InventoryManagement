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

    path('addarrivallocation',views.renderAddLocation, name="addarrivallocation"),
    path('savelocation',views.saveLocation, name="savelocation"),

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
    path('deletelocation/<int:id>',views.deleteLocation,name="deletelocation"),
    path('editlocation/<int:id>',views.renderEditLocation,name="rendereditlocation"),
    path('editarrivallocation/<int:id>',views.editArrivalLocation,name="editarrivallocation"),

    path('reportfilter',views.reportFilter, name='reportfilter'),
    path('report',views.generateReport,name='generatereport'),
    path('showdefective',views.showDefective,name='showdefective'),

    path('qualityreportfilter',views.qualityReportFilter, name='qualityreportfilter'),
    path('qualityreport',views.qualityReport,name='qualityreport'),

    path('export/excelpage', views.export_page_xls, name='excel_page'),
    path('export/excelall', views.export_all_xls, name='excel_all'),
    path('export/excelfilter', views.export_filter_all_xls, name='excel_filter_all'),

    #####################   COLOR    ###################################
    path('addcolorsupplier',views.renderAddColorSupplier,name='addcolorsupplier'),
    path('savesupplier',views.saveSupplier, name="savesupplier"),
    path('deletesupplier/<int:id>',views.deleteSupplier,name="deletesupplier"),
    path('editsupplier/<int:id>',views.renderEditSupplier,name="rendereditsupplier"),
    path('editcolorsupplier/<int:id>',views.editSupplier,name="editcolorsupplier"),
    path('addcolor',views.renderAddColor,name='addcolor'),
    path('savecolor',views.saveColor, name="savecolor"),
    path('deletecolor/<int:id>',views.deleteColor,name="deletecolor"),
    path('editcolor/<int:id>',views.renderEditColor,name="rendereditcolor"),
    path('editingcolor/<int:id>',views.editColor,name="editcolor"),

    path('placeorder',views.placeOrder,name='placeorder'),
    path('saveorder',views.saveOrder,name='saveorder'),
    path('ordergeneration',views.orderGeneration,name='ordergeneration'),

    path('goodsreceived',views.goodsReceived,name='goodsreceived'),
    path('goodsrequest',views.goodsRequest,name='goodsrequest'),
    path('goodsapprove/<int:id>',views.goods,name='goodsapprove'),
    path('goodsapproved/<int:id>',views.goodsApprove,name='approvegoods'),
]
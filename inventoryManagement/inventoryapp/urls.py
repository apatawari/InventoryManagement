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
    path('greyhome', views.greyhome,name='greyhome'),
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

    path('addchecker',views.renderAddChecker, name="addchecker"),
    path('saveChecker',views.saveChecker, name="savechecker"),
    path('deleteChecker/<int:id>',views.deleteChecker, name="deletechecker"),
    path('editchecker/<int:id>',views.renderEditChecker,name="rendereditchecker"),
    path('editgreychecker/<int:id>',views.editChecker,name="editchecker"),

    path('addtransport',views.renderAddTransport, name="addtransport"),
    path('savetransport',views.saveTransport, name="savetransport"),
    path('deletetransport/<int:id>',views.deleteTransport, name="deletetransport"),
    path('edittransport/<int:id>',views.renderEditTransport,name="renderedittransport"),
    path('editgreytransport/<int:id>',views.editTransport,name="edittransport"),

    path('addrate',views.renderAddRange, name="addrange"),
    path('saverate',views.saveRange, name="saverange"),
    path('deleterate/<int:id>',views.deleteRange, name="deleterange"),
    # path('editchecker/<int:id>',views.renderEditChecker,name="rendereditchecker"),
    # path('editgreychecker/<int:id>',views.editChecker,name="editchecker"),

    path('addarrivallocation',views.renderAddLocation, name="addarrivallocation"),
    path('savelocation',views.saveLocation, name="savelocation"),

    path('readytoprint',views.showReadyToPrint, name='readytoprint'),
    path('readytoprintrequest',views.showReadyRequest, name= "readytoprintrequest"),
    path('readyapprove/<int:id>',views.readyApprove, name='readyapprove'),
    path('sendreadytoprint/<int:id>',views.readyToPrint, name="sendreadytoprint"),
    path('back',views.back1,name="back1"),
    path('back2',views.back2checking,name="back2checking"),
    path('back/<str:state>',views.back,name="back"),
    path('backtoorders/<str:state>',views.backtoorders,name="backtoorders"),

    path('changestateback/<int:id>',views.changeStateBack,name="changestateback"),

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
    path('qualitypartyreportfilter',views.qualityReport2filter, name='qualityreport2filter'),
    path('qualitypartyreport',views.qualityReport2,name='qualityreport2'),

    path('checkerreportfilter',views.checkerReportFilter,name="checkerreportfilter"),
    path('checkerreport',views.checkerReport,name='checkerreport'),

    path('transportreportfilter',views.transportReportFilter,name="transportreportfilter"),
    path('transportreport',views.transportReport,name='transportreport'),

    path('export/excelpage', views.export_page_xls, name='excel_page'),
    path('export/excelall', views.export_all_xls, name='excel_all'),
    path('export/excelfilter', views.export_filter_all_xls, name='excel_filter_all'),

    path('export/report',views.export_report_xls,name='export_report_xls'),
    path('export/ledger',views.printLedgerExcel,name='printledgerexcel'),

    #####################   COLOR    #############################################################
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
    path('deleteorder/<int:id>',views.orderDelete,name="orderdelete"),

    path('addgodown',views.renderAddGodown,name='addgodown'),
    path('savegodown',views.saveGodown, name="savegodown"),
    path('deletegodown/<int:id>',views.deleteGodown,name="deletegodown"),
    path('editgodown/<int:id>',views.renderEditGodown,name="rendereditgodown"),
    path('editinggodown/<int:id>',views.editGodown,name="editgodown"),

    path('addlease',views.renderAddLease,name='addlease'),
    path('savelease',views.saveLease, name="savelease"),
    path('deletelease/<int:id>',views.deleteLease,name="deletelease"),
    path('editlease/<int:id>',views.renderEditLease,name="rendereditlease"),
    path('editinglease/<int:id>',views.editLease,name="editlease"),

    path('addunit',views.renderAddUnit,name='addunit'),
    path('saveunit',views.saveUnit, name="saveunit"),
    path('deleteunit/<int:id>',views.deleteUnit,name="deleteunit"),
    path('editunit/<int:id>',views.renderEditUnit,name="rendereditunit"),
    path('editingunit/<int:id>',views.editUnit,name="editunit"),

    path('colorhome', views.colorhome,name='colorhome'),

    path('placeorder',views.placeOrder,name='placeorder'),
    path('saveorder',views.saveOrder,name='saveorder'),
    path('ordergeneration',views.orderGeneration,name='ordergeneration'),
    path('orderedit/<int:id>',views.orderEdit,name="orderedit"),
    path('ordereditsave/<int:id>',views.orderEditSave,name="ordereditsave"),

    path('goodsreceived',views.goodsReceived,name='goodsreceived'),
    path('goodsrequest',views.goodsRequest,name='goodsrequest'),
    path('goodsapprove/<int:id>',views.goods,name='goodsapprove'),
    path('viewgoodorder/<int:id>',views.viewOrder,name='vieworder'),
    path('validateorder/<int:id>',views.renderValidate,name='validateorder'),
    path('validate/<int:id>',views.validate,name='validate'),
    path('goodsapproved/<int:id>',views.goodsApprove,name='approvegoods'),

    path('goodslease',views.goodsLease,name='goodslease'),
    path('leaserequest',views.leaseRequest,name='leaserequest'),
    path('leaseapprove/<int:id>',views.viewGood,name='leaseapprove'),
    path('leaseapproved/<int:id>',views.leaseApprove,name='leaseapproved'),
    path('leaseedit/<int:id>',views.leaseedit,name='leaseedit'),
    path('saveleaseedit/<int:id>',views.savelease,name='savelease'),
    path('changeloosegodown/<int:id>',views.changeLooseGodown,name='changeloosegodown'),
    path('savechangeloosegodown/<int:id>',views.savechangeLooseGodown,name='savechangeloosegodown'),

    path('dailyconsumption1',views.renderDailyConsumptionLease1,name='dailyconsumption'),
    path('dailyconsumption2',views.renderDailyConsumptionLease2,name='dailyconsumption2'),
    path('dailyconsumptiondetails',views.dailyconsumptionDetails,name='dailyconsumptiondetails'),
    path('dailyconsumptiondetails2',views.dailyconsumptionDetails2,name='dailyconsumptiondetails2'),
    path('editdailyconsumption/<int:id>',views.editDailyConsumption,name='editdailyconsumption'),
    path('savedailyconsumption/<int:id>',views.saveDailyConsumption,name='savedailyconsumption'),
    path('backdailyconsumption',views.backToDailyConsumption,name='backtodailydetails'),
    path('consume/<str:name>',views.consume,name='consume'),
    path('closingstock',views.renderClosingStock,name='closingstock'),

    path('colorreportfilter',views.renderColorReportFilter,name='colorreportfilter'),
    path('colorreport',views.colorReport,name='colorreport'),

    ############################################# Module 3 - Employee ################################################
    path('employeehome', views.employeehome,name='employeehome'),
    path('saveemployee', views.saveEmployee,name='saveemployee'),
    path('employeedetails', views.employeedetails,name='employeedetails'),
    path('deleteemployee/<int:id>', views.deleteEmployee,name='deleteemployee'),
    path('editemployee/<int:id>', views.renderEditEmployee,name='editemployee'),
    path('saveeditemployee/<int:id>', views.saveEditEmployee,name='saveeditemployee'),
    path('addbank', views.renderAddBankAc,name='addbank'),
    path('savebank', views.saveBank,name='savebank'),
    path('deletebank/<int:id>', views.deleteBank,name='deletebank'),
    path('editbank/<int:id>', views.renderEditBank,name='editbank'),
    path('bankedit/<int:id>', views.editBank,name='bankedit'),

    path('addcity', views.renderAddCity,name='addcity'),
    path('savecity', views.saveCity,name='savecity'),
    path('deletecity/<int:id>', views.deleteCity,name='deletecity'),
    path('editcity/<int:id>', views.renderEditCity,name='editcity'),
    path('cityedit/<int:id>', views.editCity,name='cityedit'),

    path('addemployeecategory', views.renderAddEmpCategory,name='addempcategory'),
    path('saveempcategory', views.saveEmpCategory,name='saveempcategory'),
    path('deleteempcategory/<int:id>', views.deleteEmpCategory,name='deleteempcategory'),
    path('editemployeecategory/<int:id>', views.renderEditEmpCategory,name='editempcategory'),
    path('empcategoryedit/<int:id>', views.editEmpCategory,name='empcategoryedit'),

    path('paymentgenerationform', views.renderGeneratorForm,name='generatorform'),
    path('generatepayment', views.generatePayment,name='generatepayment'),
    path('makepayment', views.makePayment,name='makepayment'),

    path('banksheet', views.bankSheet,name='banksheet'),
    path('banksheetfiltered', views.bankSheet2,name='banksheet2'),
    path('salarysheet', views.salarySheet,name='salarysheet'),
    path('salarysheetfiltered', views.salarySheet2,name='salarysheet2'),
]
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('index', views.index,name='index'),
    path('insert', views.upload,name='insert'),
    path('intransit',views.showIntransit, name='intransit'),
    path('<int:id>',views.record, name='record'),

]
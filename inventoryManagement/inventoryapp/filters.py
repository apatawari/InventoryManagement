from .models import Record,ColorRecord,AllOrders,GodownLeaseColors
import django_filters
from django.db import models
from django import forms

class RecordFilter(django_filters.FilterSet):
    class Meta:
        model=Record
        fields = {
            'party_name': [ 'contains','exact'],
            'lot_no': ['exact', 'contains'],
            'quality': ['exact'],
            'lr_no': ['exact', 'contains'],
        }

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            }
        }

class ColorFilter(django_filters.FilterSet):
    class Meta:
        model=ColorRecord
        fields = {
            'supplier': [ 'exact'],
            'order_no': ['exact', 'contains'],
            'color': ['exact'],
            'godown': ['exact'],
            'lease': ['exact', 'contains']
        }

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            }
        }

class ColorOrderFilter(django_filters.FilterSet):
    class Meta:
        model=AllOrders
        fields = {
            'supplier': [ 'exact'],
            'order_no': ['exact', 'contains'],
            'color': ['exact']
        }

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            }
        }

class GodownLeaseFilter(django_filters.FilterSet):
    class Meta:
        model=GodownLeaseColors
        fields = {
            'color': [ 'exact'],
            'state': ['exact'],
            'loose_godown_state': ['exact']
        }

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            }
        }
from .models import Record
import django_filters
from django.db import models

class RecordFilter(django_filters.FilterSet):
    class Meta:
        model=Record
        fields = {
            'party_name': [ 'contains','exact'],
            'lot_no': ['exact', 'contains'],
            'quality': ['exact', 'contains'],
        }

        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            }
        }
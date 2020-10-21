from .models import Record
import django_filters


class RecordFilter(django_filters.FilterSet):
    class Meta:
        model=Record
        fields = {
            'party_name': [ 'contains','exact'],
            'lot_no': ['exact', 'contains'],
            'quality': ['exact', 'contains'],
        }

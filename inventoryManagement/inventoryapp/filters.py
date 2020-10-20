from .models import Record
import django_filters


class RecordFilter(django_filters.FilterSet):
    class Meta:
        model=Record
        fields = {
            'party_name': ['exact', 'contains'],
            'lot_no': ['exact', 'contains'],
            'quality': ['exact', 'contains'],
        }

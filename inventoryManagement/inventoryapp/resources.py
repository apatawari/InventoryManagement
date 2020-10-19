from import_export import resources
from .models import Record

class ItemResources(resources.ModelResource):
    class meta:
        model=Record
        import_id_fields=('S.No')
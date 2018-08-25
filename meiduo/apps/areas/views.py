from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Area
from .serializers import AreaSerializer,SubAreaSerializer
from rest_framework_extensions.cache.mixins import CacheResponseMixin


class AreasViewSet(CacheResponseMixin,ReadOnlyModelViewSet):
    """
    行政区划信息
    """
    pagination_class = None  # 区划信息不分页class AreasViewSet(,ReadOnlyModelViewSet):


    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubAreaSerializer
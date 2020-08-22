import structlog
from rest_framework import generics


logger = structlog.get_logger(__name__)


class PermissionedListCreateAPIView(generics.ListCreateAPIView):

    def filter_queryset(self, queryset):
        filtered = super().filter_queryset(queryset)
        perm = self.permission()
        my_ids = {
            record.pk
            for record in filtered
            if perm.has_object_permission(self.request, self, record)
        }
        return filtered.filter(pk__in=my_ids).order_by('created_at')

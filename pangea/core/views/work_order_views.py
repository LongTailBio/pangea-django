import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from ..models import (
    JobOrder,
    WorkOrder,
    JobOrderProto,
    WorkOrderProto,
    Sample,
)
from ..serializers import (
    WorkOrderProtoSerializer,
    JobOrderProtoSerializer,
    WorkOrderSerializer,
    JobOrderSerializer,
)
from ..permissions import WorkOrderPermission, JobOrderPermission, SamplePermission

logger = structlog.get_logger(__name__)


class WorkOrderProtoListView(generics.ListAPIView):
    queryset = WorkOrderProto.objects.all().order_by('created_at')
    serializer_class = WorkOrderProtoSerializer
    filterset_fields = ['uuid', 'name']


class WorkOrderProtoRetrieveView(generics.RetrieveAPIView):
    queryset = WorkOrderProto.objects.all().order_by('created_at')
    serializer_class = WorkOrderProtoSerializer


class JobOrderProtoListView(generics.ListAPIView):
    queryset = JobOrderProto.objects.all().order_by('created_at')
    serializer_class = JobOrderProtoSerializer
    filterset_fields = ['uuid', 'name']


class JobOrderProtoRetrieveView(generics.RetrieveAPIView):
    queryset = JobOrderProto.objects.all().order_by('created_at')
    serializer_class = JobOrderProtoSerializer


class WorkOrderRetrieveView(generics.RetrieveAPIView):
    queryset = WorkOrder.objects.all().order_by('created_at')
    serializer_class = WorkOrderSerializer
    permission_classes = (WorkOrderPermission,)


class JobOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = JobOrder.objects.all().order_by('created_at')
    serializer_class = JobOrderSerializer
    permission_classes = (JobOrderPermission,)


class WorkOrderProtoWorkOrderView(generics.ListAPIView):
    """This class handles managing membership of samples within sample groups."""
    queryset = WorkOrder.objects.all().order_by('created_at')
    serializer_class = WorkOrderSerializer

    def filter_queryset(self, queryset):
        work_order_proto_uuid = self.kwargs.get('pk')
        work_order_proto = WorkOrderProto.objects.get(pk=work_order_proto_uuid)
        if not work_order_proto.user_is_privileged(self.request.user):
            return []
        work_orders = super().filter_queryset(queryset).filter(prototype__pk=work_order_proto_uuid)
        return work_orders.order_by('created_at')


class SampleWorkOrdersView(generics.ListAPIView):
    """This class handles managing membership of samples within sample groups."""
    permission_classes = (WorkOrderPermission,)
    queryset = WorkOrder.objects.all().order_by('created_at')
    serializer_class = WorkOrderSerializer

    def filter_queryset(self, queryset):
        sample_uuid = self.kwargs.get('sample_pk')
        sample = Sample.objects.get(pk=sample_uuid)
        if not SamplePermission().has_object_permission(self.request, self, sample):
            raise PermissionDenied(_('Insufficient permissions to view work order for sample.'))
        work_orders = super().filter_queryset(queryset).filter(sample__pk=sample_uuid)
        return work_orders.order_by('created_at')


@api_view(['POST'])
def create_new_work_order(request, sample_pk, wop_pk):
    sample = Sample.objects.get(pk=sample_pk)
    try:
        authorized = request.user.organization_set.filter(
            pk=sample.library.group.organization.pk
        ).exists()
    except AttributeError:  # occurs if user is not logged in
        authorized = False
    if not authorized:
        raise PermissionDenied(_('Insufficient permissions to generate work order for sample.'))
    work_order_proto = WorkOrderProto.objects.get(pk=wop_pk)
    work_order = work_order_proto.work_order(sample)
    blob = {'uuid': work_order.uuid}

    return Response(blob, status=201)

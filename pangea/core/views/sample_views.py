import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .utils import PermissionedListCreateAPIView
from ..param_auth import TokenParamAuthentication
from ..models import (
    Sample,
)
from ..permissions import (
    SamplePermission,
)
from ..serializers import (
    SampleSerializer,
    SampleAnalysisResultSerializer,
    SampleAnalysisResultFieldSerializer,
)


logger = structlog.get_logger(__name__)


class SampleCreateView(PermissionedListCreateAPIView):
    queryset = Sample.objects.all().order_by('created_at')
    serializer_class = SampleSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'library_id', 'name']
    permission = SamplePermission

    def perform_create(self, serializer):
        organization = serializer.validated_data.get('library').group.organization
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.warning(
                'attempted_create_sample_without_permission',
                user=self.request.user,
                organization_pk=organization.pk,
            )
            raise PermissionDenied(_('Organization membership is required to create a sample.'))
        sample = serializer.save()
        sample_group = serializer.validated_data.get('library').group
        sample.sample_groups.add(sample_group)


class SampleDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    permission_classes = (SamplePermission,)


@api_view(['GET'])
@authentication_classes([TokenParamAuthentication])
def get_sample_manifest(request, pk):
    """Reply with a sample group manifest."""
    sample = Sample.objects.get(pk=pk)
    mygrp = sample.library.group
    if not mygrp.is_public:
        try:
            membership_queryset = request.user.organization_set.filter(pk=mygrp.organization.pk)
            authorized = membership_queryset.exists()
        except AttributeError:  # occurs if user is not logged in
            authorized = False
        if not authorized:
            raise PermissionDenied(_('Insufficient permissions to get group manifest.'))
    blob = SampleSerializer(sample).data
    blob['analysis_results'] = []
    for ar in sample.analysis_result_set.all():
        ar_blob = SampleAnalysisResultSerializer(ar).data
        del ar_blob['sample_obj']
        ar_blob['fields'] = []
        for field in ar.fields.all():
            field_blob = SampleAnalysisResultFieldSerializer(field).data
            del field_blob['analysis_result_obj']
            ar_blob['fields'].append(field_blob)
        blob['analysis_results'].append(ar_blob)

    return Response(blob)

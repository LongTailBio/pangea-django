import structlog
import pandas as pd
import json

from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.views.decorators.http import require_GET
from django.http import HttpResponse

from rest_framework import generics
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated

from .utils import PermissionedListCreateAPIView
from ..param_auth import TokenParamAuthentication
from ..models import (
    SampleGroup,
    Sample,
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
)
from ..permissions import (
    SampleGroupPermission,
    SamplePermission,
)
from ..serializers import (
    SampleGroupSerializer,
    SampleGroupAddSampleSerializer,
    SampleSerializer,
    SampleAnalysisResultSerializer,
    SampleGroupAnalysisResultSerializer,
    SampleAnalysisResultFieldSerializer,
    SampleGroupAnalysisResultFieldSerializer,
)


logger = structlog.get_logger(__name__)


class SampleGroupCreateView(PermissionedListCreateAPIView):
    queryset = SampleGroup.objects.all().order_by('created_at')
    serializer_class = SampleGroupSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'organization_id', 'name', 'is_public']
    permission = SampleGroupPermission

    def perform_create(self, serializer):
        """Require organization membership to create sample group."""
        organization = serializer.validated_data.get('organization')
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.warning(
                'attempted_create_sample_group_without_permission',
                organization={'uuid': organization.pk, 'name': organization.name},
            )
            raise PermissionDenied(_('Organization membership is required to create a sample group.'))
        serializer.save()


class SampleGroupDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = SampleGroup.objects.all()
    serializer_class = SampleGroupSerializer
    permission_classes = (SampleGroupPermission,)


class SampleGroupSamplesView(generics.ListAPIView):
    """This class handles managing membership of samples within sample groups."""
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Sample.objects.all().order_by('created_at')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SampleSerializer
        if self.request.method == 'POST':
            return SampleGroupAddSampleSerializer

    def _filter_queryset_library(self, queryset, sample_grp_uuid, sample_grp, perm):
        """
        if the group is a library it should not have samples from other groups
        so we only check this group
        """
        has_permission = perm.has_object_permission(self.request, self, sample_grp)
        if not has_permission:
            return []
        samples = super().filter_queryset(queryset).filter(sample_groups__pk=sample_grp_uuid)
        return samples.order_by('created_at')

    def filter_queryset(self, queryset):
        sample_grp_uuid = self.kwargs.get('group_pk')
        sample_group = SampleGroup.objects.get(pk=sample_grp_uuid)
        perm, has_permission = SampleGroupPermission(), True
        if sample_group.is_library:
            return self._filter_queryset_library(
                queryset, sample_grp_uuid, sample_group, perm
            )
        samples = super().filter_queryset(queryset).filter(sample_groups__pk=sample_grp_uuid)
        libraries = {samp.library.group for samp in samples}
        for lib in libraries:
            has_permission &= perm.has_object_permission(self.request, self, lib)
        if not has_permission:
            return []
        return samples.order_by('created_at')

    def post(self, request, *args, **kwargs):
        sample_group_uuid = kwargs.get('group_pk')
        sample_uuid = request.data.get('sample_uuid', None)
        sample_group = SampleGroup.objects.get(pk=sample_group_uuid)
        sample = Sample.objects.get(pk=sample_uuid)

        group_org = sample_group.organization
        group_membership_queryset = self.request.user.organization_set.filter(pk=group_org.pk)
        sample_org = sample.library.group.organization
        sample_membership_queryset = self.request.user.organization_set.filter(pk=sample_org.pk)

        if not group_membership_queryset.exists() or not sample_membership_queryset.exists():
            logger.info(
                'attempted_add_sample_to_group_without_permission',
                user=request.user,
                sample_pk=sample.pk,
                sample_group_pk=sample_group.pk,
            )
            raise PermissionDenied(_('Insufficient permissions to add sample to sample group.'))

        sample.sample_groups.add(sample_group)
        return Response({"status": "success"})


@api_view(['GET'])
@authentication_classes([TokenParamAuthentication])
def get_sample_metadata_in_group(request, pk):
    """Reply with metadata for samples in group."""
    grp = SampleGroup.objects.get(pk=pk)
    if not grp.is_public:
        try:
            membership_queryset = request.user.organization_set.filter(pk=grp.organization.pk)
            authorized = membership_queryset.exists()
        except AttributeError:  # occurs if user is not logged in
            authorized = False
        if not authorized:
            raise PermissionDenied(_('Insufficient permissions to access group.'))
    metadata = {}
    for sample in grp.sample_set.all():
        metadata[sample.name] = sample.metadata

    if request.GET.get('kind', None) == 'csv':
        tbl = pd.DataFrame.from_dict(metadata, orient='index')
        metadata = tbl.to_csv()
        response = HttpResponse(content=metadata, content_type='text/csv')
        grp_name = grp.name.replace(' ', '_')
        response['Content-Disposition'] = f'attachment; filename="{grp_name}_metadata.csv"'
        return response

    return HttpResponse(json.dumps(metadata), content_type="application/json")


@api_view(['GET'])
@authentication_classes([TokenParamAuthentication])
def get_sample_ar_counts_in_group(request, pk):
    """Reply with counts for all types of sample analysis results in the group."""
    grp = SampleGroup.objects.get(pk=pk)
    if not grp.is_public:
        try:
            membership_queryset = request.user.organization_set.filter(pk=grp.organization.pk)
            authorized = membership_queryset.exists()
        except AttributeError:  # occurs if user is not logged in
            authorized = False
        if not authorized:
            raise PermissionDenied(_('Insufficient permissions to access group.'))
    blob = {'n_samples': 0}
    for sample in grp.sample_set.all():
        blob['n_samples'] += 1
        for module_name in {ar.module_name for ar in sample.analysis_result_set.all()}:
            blob[module_name] = 1 + blob.get(module_name, 0)

    return Response(blob)


@api_view(['GET'])
@authentication_classes([TokenParamAuthentication])
def get_sample_group_manifest(request, pk):
    """Reply with a sample group manifest."""
    grp = SampleGroup.objects.get(pk=pk)
    if not grp.is_public:
        try:
            membership_queryset = request.user.organization_set.filter(pk=grp.organization.pk)
            authorized = membership_queryset.exists()
        except AttributeError:  # occurs if user is not logged in
            authorized = False
        if not authorized:
            raise PermissionDenied(_('Insufficient permissions to get group manifest.'))
    blob = SampleGroupSerializer(grp).data
    blob['samples'] = []
    for sample in grp.sample_set.all():
        sample_blob = SampleSerializer(sample).data
        del sample_blob['library_obj']
        sample_blob['analysis_results'] = []
        for ar in sample.analysis_result_set.all():
            ar_blob = SampleAnalysisResultSerializer(ar).data
            del ar_blob['sample_obj']
            ar_blob['fields'] = []
            for field in ar.fields.all():
                field_blob = SampleAnalysisResultFieldSerializer(field).data
                del field_blob['analysis_result_obj']
                ar_blob['fields'].append(field_blob)
            sample_blob['analysis_results'].append(ar_blob)
        blob['samples'].append(sample_blob)

    blob['analysis_results'] = []
    for ar in grp.analysis_result_set.all():
        ar_blob = SampleGroupAnalysisResultSerializer(ar).data
        del ar_blob['sample_group_obj']
        ar_blob['fields'] = []
        for field in ar.fields.all():
            field_blob = SampleGroupAnalysisResultFieldSerializer(field).data
            del field_blob['analysis_result_obj']
            ar_blob['fields'].append(field_blob)
        blob['analysis_results'].append(ar_blob)

    return Response(blob)

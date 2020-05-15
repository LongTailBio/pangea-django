import structlog
import pandas as pd
import json

from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.views.decorators.http import require_GET

from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated

from .models import (
    PangeaUser,
    Organization,
    S3ApiKey,
    SampleGroup,
    Sample,
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
)
from .permissions import (
    OrganizationPermission,
    S3ApiKeyPermission,
    SampleGroupPermission,
    SamplePermission,
    SampleAnalysisResultPermission,
    SampleGroupAnalysisResultPermission,
    SampleAnalysisResultFieldPermission,
    SampleGroupAnalysisResultFieldPermission,
)
from .serializers import (
    PangeaUserSerializer,
    OrganizationSerializer,
    S3ApiKeySerializer,
    OrganizationAddUserSerializer,
    SampleGroupSerializer,
    SampleGroupAddSampleSerializer,
    SampleSerializer,
    SampleAnalysisResultSerializer,
    SampleGroupAnalysisResultSerializer,
    SampleAnalysisResultFieldSerializer,
    SampleGroupAnalysisResultFieldSerializer,
)

logger = structlog.get_logger(__name__)


class OrganizationCreateView(generics.ListCreateAPIView):
    queryset = Organization.objects.all().order_by('created_at')
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'name']

    def perform_create(self, serializer):
        """Require valid session to create organization."""
        organization = serializer.save()
        self.request.user.organization_set.add(organization)


class OrganizationUsersView(generics.ListAPIView):
    """This class handles managing membership of users within organizations."""
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PangeaUserSerializer
        if self.request.method == 'POST':
            return OrganizationAddUserSerializer

    def get_queryset(self):
        """Limit sample queryset to samples in the specified sample group."""
        organization_uuid = self.kwargs['organization_pk']
        return PangeaUser.objects.filter(organization__pk=organization_uuid).order_by('date_joined')

    def post(self, request, *args, **kwargs):
        organization_uuid = kwargs.get('organization_pk')
        organization = Organization.objects.get(pk=organization_uuid)

        org_membership_queryset = self.request.user.organization_set.filter(pk=organization_uuid)
        if not org_membership_queryset.exists():
            logger.info(
                'attempted_add_user_to_organization_without_permission',
                auth_user=request.user,
                organization_pk=organization.pk,
                user_pk=request.data.get('user', None),
            )
            raise PermissionDenied(_('Insufficient permissions to add user to organization.'))

        serializer = OrganizationAddUserSerializer(data=request.data)
        if (serializer.is_valid()):
            user = serializer.validated_data.get('user')
            organization.users.add(user)
            return Response({ "status": "success" })
        else:
            return Response(serializer.errors, status=400)


class OrganizationDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (OrganizationPermission,)


class S3ApiKeyCreateView(generics.ListCreateAPIView):
    serializer_class = S3ApiKeySerializer
    permission_classes = (IsAuthenticated, S3ApiKeyPermission)

    def get_queryset(self):
        perm = S3ApiKeyPermission()
        s3_ids = {
            s3.pk
            for s3 in S3ApiKey.objects.all()
            if perm.has_object_permission(self.request, self, s3)
        }
        return S3ApiKey.objects.filter(pk__in=s3_ids).order_by('created_at')

    def perform_create(self, serializer):
        """Require organization membership to create sample group."""
        organization = serializer.validated_data.get('organization')
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.warning(
                'attempted_create_s3apikey_without_permission',
                organization={'uuid': organization.pk, 'name': organization.name},
            )
            raise PermissionDenied(_('Organization membership is required to create an s3 api key.'))
        serializer.save()


class S3ApiKeyDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = S3ApiKeySerializer
    permission_classes = (S3ApiKeyPermission, IsAuthenticated)

    def get_queryset(self):
        perm = S3ApiKeyPermission()
        s3_ids = {
            s3.pk
            for s3 in S3ApiKey.objects.all()
            if perm.has_object_permission(self.request, self, s3)
        }
        return S3ApiKey.objects.filter(pk__in=s3_ids).order_by('created_at')


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

    def filter_queryset(self, queryset):
        filtered = super().filter_queryset(queryset)
        perm = SamplePermission()
        sample_group_uuid = self.kwargs['group_pk']
        my_ids = {
            samp.pk
            for samp in filtered.filter(sample_groups__pk=sample_group_uuid)
            if perm.has_object_permission(self.request, self, samp)
        }
        return filtered.filter(pk__in=my_ids).order_by('created_at')

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
        return Response({ "status": "success" })


@require_GET
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

    if request.GET.get('format', None) == 'csv':
        tbl = pd.DataFrame.from_dict(metadata, orient='index')
        metadata = tbl.to_csv()
        response = HttpResponse(content=metadata, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{grp.name}_metadata.csv"'
        return response

    return HttpResponse(json.dumps(metadata), content_type="application/json")


@api_view(['GET'])
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


class SampleAnalysisResultCreateView(PermissionedListCreateAPIView):
    queryset = SampleAnalysisResult.objects.all()
    serializer_class = SampleAnalysisResultSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    filterset_fields = ['uuid', 'sample_id', 'module_name', 'replicate']
    permission = SampleAnalysisResultPermission

    def perform_create(self, serializer):
        organization = serializer.validated_data.get('sample').library.group.organization
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.warning(
                'attempted_create_sample_analysis_result_without_permission',
                organization={'uuid': organization.pk, 'name': organization.name},
            )
            raise PermissionDenied(_('Organization membership is required to create a sample analysis result.'))
        serializer.save()


class SampleAnalysisResultDetailsView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SampleAnalysisResult.objects.all()
    serializer_class = SampleAnalysisResultSerializer
    permission_classes = (SampleAnalysisResultPermission,)


class SampleGroupAnalysisResultCreateView(PermissionedListCreateAPIView):
    queryset = SampleGroupAnalysisResult.objects.all().order_by('created_at')
    serializer_class = SampleGroupAnalysisResultSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'sample_group_id', 'module_name', 'replicate']
    permission = SampleGroupAnalysisResultPermission

    def perform_create(self, serializer):
        organization = serializer.validated_data.get('sample_group').organization
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.warning(
                'attempted_create_sample_group_analysis_result_without_permission',
                user=self.request.user,
                organization_pk=organization.pk,
            )
            raise PermissionDenied(_('Organization membership is required to create a sample group analysis result.'))
        serializer.save()


class SampleGroupAnalysisResultDetailsView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SampleGroupAnalysisResult.objects.all()
    serializer_class = SampleGroupAnalysisResultSerializer
    permission_classes = (SampleGroupAnalysisResultPermission,)


class SampleAnalysisResultFieldCreateView(PermissionedListCreateAPIView):
    queryset = SampleAnalysisResultField.objects.all().order_by('created_at')
    serializer_class = SampleAnalysisResultFieldSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'name', 'analysis_result_id']
    permission = SampleAnalysisResultFieldPermission

    def perform_create(self, serializer):
        organization = serializer.validated_data.get('analysis_result') \
            .sample.library.group.organization
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.warning(
                'attempted_create_sample_analysis_result_field_without_permission',
                organization={'uuid': organization.pk, 'name': organization.name},
            )
            raise PermissionDenied(_('Organization membership is required to create a sample analysis result field.'))
        serializer.save()


class SampleAnalysisResultFieldDetailsView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SampleAnalysisResultField.objects.all()
    serializer_class = SampleAnalysisResultFieldSerializer
    permission_classes = (SampleAnalysisResultFieldPermission,)


class SampleGroupAnalysisResultFieldCreateView(PermissionedListCreateAPIView):
    queryset = SampleGroupAnalysisResultField.objects.all().order_by('created_at')
    serializer_class = SampleGroupAnalysisResultFieldSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'name', 'analysis_result_id']
    permission = SampleGroupAnalysisResultFieldPermission

    def perform_create(self, serializer):
        organization = serializer.validated_data.get('analysis_result').sample_group.organization
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.info(
                'attempted_create_sample_group_analysis_result_without_permission',
                user=self.request.user,
                organization_pk=organization.pk,
            )
            raise PermissionDenied(_('Organization membership is required to create a sample group analysis result field.'))
        serializer.save()


class SampleGroupAnalysisResultFieldDetailsView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SampleGroupAnalysisResultField.objects.all()
    serializer_class = SampleGroupAnalysisResultFieldSerializer
    permission_classes = (SampleGroupAnalysisResultFieldPermission,)

import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .utils import PermissionedListCreateAPIView
from ..models import (
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
)
from ..permissions import (
    SampleAnalysisResultPermission,
    SampleGroupAnalysisResultPermission,
    SampleAnalysisResultFieldPermission,
    SampleGroupAnalysisResultFieldPermission,
)
from ..serializers import (
    SampleAnalysisResultSerializer,
    SampleGroupAnalysisResultSerializer,
    SampleAnalysisResultFieldSerializer,
    SampleGroupAnalysisResultFieldSerializer,
)


logger = structlog.get_logger(__name__)



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


def authorize_sample_ar_upload_url(request, pk):
    arf = SampleAnalysisResultField.objects.get(pk=pk)
    mygrp = arf.analysis_result.sample.library.group
    if not mygrp.is_public:
        try:
            membership_queryset = request.user.organization_set.filter(pk=mygrp.organization.pk)
            authorized = membership_queryset.exists()
        except AttributeError:  # occurs if user is not logged in
            authorized = False
        if not authorized:
            raise PermissionDenied(_('Insufficient permissions to get upload url.'))
    return arf


@api_view(['POST'])
def post_sample_ar_upload_url(request, pk):
    """Reply with a sample group manifest."""
    arf = authorize_sample_ar_upload_url(request, pk)
    if arf.field_type != 's3':
        arf.as_s3_link(request.data['filename'])
    stance = request.data.get('stance', 'upload')
    n_parts = request.data.get('n_parts', 1)
    blob = arf.get_presigned_upload_url(stance=stance, n_parts=n_parts)
    return Response(blob)


@api_view(['POST'])
def post_sample_ar_complete_multipart_upload_url(request, pk):
    """Reply with a sample group manifest."""
    arf = authorize_sample_ar_upload_url(request, pk)
    upload_id, parts = request.data['upload_id'], request.data['parts']
    blob = arf.get_presigned_completion_url(upload_id, parts)
    return Response(blob)


def authorize_sample_group_ar_upload_url(request, pk):
    arf = SampleGroupAnalysisResultField.objects.get(pk=pk)
    mygrp = arf.analysis_result.sample.library.group
    if not mygrp.is_public:
        try:
            membership_queryset = request.user.organization_set.filter(pk=mygrp.organization.pk)
            authorized = membership_queryset.exists()
        except AttributeError:  # occurs if user is not logged in
            authorized = False
        if not authorized:
            raise PermissionDenied(_('Insufficient permissions to get upload url.'))
    return arf


@api_view(['POST'])
def post_sample_group_ar_upload_url(request, pk):
    """Reply with a sample group manifest."""
    arf = authorize_sample_group_ar_upload_url(request, pk)
    if arf.field_type != 's3':
        arf.as_s3_link(request.data['filename'])
    stance = request.data.get('stance', 'upload')
    n_parts = request.data.get('n_parts', 1)
    blob = arf.get_presigned_upload_url(stance=stance, n_parts=n_parts)
    return Response(blob)


@api_view(['POST'])
def post_sample_group_ar_complete_multipart_upload_url(request, pk):
    """Reply with a sample group manifest."""
    arf = authorize_sample_group_ar_upload_url(request, pk)
    upload_id, parts = request.data['upload_id'], request.data['parts']
    blob = arf.get_presigned_completion_url(upload_id, parts)
    return Response(blob)



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

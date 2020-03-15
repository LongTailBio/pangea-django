import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import (
    PangeaUser,
    Organization,
    SampleGroup,
    Sample,
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
)
from .permissions import (
    OrganizationPermission,
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


class SampleGroupCreateView(generics.ListCreateAPIView):
    queryset = SampleGroup.objects.all().order_by('created_at')
    serializer_class = SampleGroupSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'organization_id', 'name', 'is_public']

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

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SampleSerializer
        if self.request.method == 'POST':
            return SampleGroupAddSampleSerializer

    def get_queryset(self):
        """Limit sample queryset to samples in the specified sample group."""
        sample_group_uuid = self.kwargs['group_pk']
        return Sample.objects.filter(sample_groups__pk=sample_group_uuid).order_by('created_at')

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


class SampleCreateView(generics.ListCreateAPIView):
    queryset = Sample.objects.all().order_by('created_at')
    serializer_class = SampleSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'library_id', 'name']

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


class SampleAnalysisResultCreateView(generics.ListCreateAPIView):
    queryset = SampleAnalysisResult.objects.all().order_by('created_at')
    serializer_class = SampleAnalysisResultSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'sample_id', 'module_name', 'replicate']

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


class SampleGroupAnalysisResultCreateView(generics.ListCreateAPIView):
    queryset = SampleGroupAnalysisResult.objects.all().order_by('created_at')
    serializer_class = SampleGroupAnalysisResultSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'sample_group_id', 'module_name', 'replicate']

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


class SampleAnalysisResultFieldCreateView(generics.ListCreateAPIView):
    queryset = SampleAnalysisResultField.objects.all()
    serializer_class = SampleAnalysisResultFieldSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'name', 'analysis_result_id']

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


class SampleGroupAnalysisResultFieldCreateView(generics.ListCreateAPIView):
    queryset = SampleGroupAnalysisResultField.objects.all()
    serializer_class = SampleGroupAnalysisResultFieldSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'name', 'analysis_result_id']

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

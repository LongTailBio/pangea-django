import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import (
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
    OrganizationSerializer,
    SampleGroupSerializer,
    SampleSerializer,
    SampleAnalysisResultSerializer,
    SampleGroupAnalysisResultSerializer,
    SampleAnalysisResultFieldSerializer,
    SampleGroupAnalysisResultFieldSerializer,
)

logger = structlog.get_logger(__name__)


class OrganizationCreateView(generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        """Require valid session to create organization."""
        organization = serializer.save()
        self.request.user.organization_set.add(organization)


class OrganizationDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (OrganizationPermission,)


class SampleGroupCreateView(generics.ListCreateAPIView):
    queryset = SampleGroup.objects.all()
    serializer_class = SampleGroupSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

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


class SampleCreateView(generics.ListCreateAPIView):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

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
        serializer.save()


class SampleDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    permission_classes = (SamplePermission,)


class SampleAnalysisResultCreateView(generics.ListCreateAPIView):
    queryset = SampleAnalysisResult.objects.all()
    serializer_class = SampleAnalysisResultSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

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
    queryset = SampleGroupAnalysisResult.objects.all()
    serializer_class = SampleGroupAnalysisResultSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

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

    def perform_create(self, serializer):
        organization = serializer.validated_data.get('analysis_result').sample_group.organization
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.warning(
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


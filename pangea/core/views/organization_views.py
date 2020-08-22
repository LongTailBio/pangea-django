import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated

from ..models import (
    PangeaUser,
    Organization,
    S3ApiKey,
)
from ..permissions import (
    OrganizationPermission,
    S3ApiKeyPermission,
)
from ..serializers import (
    PangeaUserSerializer,
    OrganizationSerializer,
    S3ApiKeySerializer,
    OrganizationAddUserSerializer,
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
            return Response({"status": "success"})
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

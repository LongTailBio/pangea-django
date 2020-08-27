import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from ..models import (
    S3ApiKey,
    S3Bucket,
)
from ..permissions import (
    S3ApiKeyPermission,
    S3BucketPermission,
)
from ..serializers import (
    S3ApiKeySerializer,
    S3BucketSerializer,
)


logger = structlog.get_logger(__name__)


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
        """Require organization membership to create S3 API Key."""
        bucket = serializer.validated_data.get('bucket')
        organization = bucket.organization
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


class S3BucketCreateView(generics.ListCreateAPIView):
    serializer_class = S3BucketSerializer
    permission_classes = (IsAuthenticated, S3BucketPermission)

    def get_queryset(self):
        perm = S3BucketPermission()
        s3_ids = {
            s3.pk
            for s3 in S3Bucket.objects.all()
            if perm.has_object_permission(self.request, self, s3)
        }
        return S3Bucket.objects.filter(pk__in=s3_ids).order_by('created_at')

    def perform_create(self, serializer):
        """Require organization membership to create S3 bucket."""
        organization = serializer.validated_data.get('organization')
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.warning(
                'attempted_create_s3bucket_without_permission',
                organization={'uuid': organization.pk, 'name': organization.name},
            )
            raise PermissionDenied(_('Organization membership is required to create an s3 bucket.'))
        serializer.save()


class S3BucketDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = S3BucketSerializer
    permission_classes = (S3BucketPermission, IsAuthenticated)

    def get_queryset(self):
        perm = S3BucketPermission()
        s3_ids = {
            s3.pk
            for s3 in S3Bucket.objects.all()
            if perm.has_object_permission(self.request, self, s3)
        }
        return S3Bucket.objects.filter(pk__in=s3_ids).order_by('created_at')

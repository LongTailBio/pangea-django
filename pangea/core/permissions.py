
import structlog
from rest_framework import permissions


logger = structlog.get_logger(__name__)


class OrganizationPermission(permissions.BasePermission):
    """Require organization membership in order to modify organization."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            logger.info(
                'user_missing_or_not_authenticated',
                request={
                    'method': request.method,
                    'user': request.user,
                    'user_is_authenticated': request.user.is_authenticated,
                }
            )
            return False

        # Require organization membership to edit/delete
        has_org_membership = view.get_queryset().filter(users=request.user).exists()
        if not has_org_membership:
            logger.info(
                'required_organization_membership_not_found',
                request={
                    'method': request.method,
                    'user': request.user,
                    'user_is_authenticated': request.user.is_authenticated,
                }
            )
        return has_org_membership


class S3ApiKeyPermission(permissions.BasePermission):
    """Require organization membership in order to do anything with s3 API keys."""

    def has_object_permission(self, request, view, obj):
        if not bool(request.user and request.user.is_authenticated):
            logger.info(
                's3_permission_user_missing_or_not_authenticated',
                request={
                    'method': request.method,
                    'user': request.user,
                    'user_is_authenticated': request.user.is_authenticated,
                }
            )
            return False

        has_org_membership = request.user in obj.bucket.organization.users.all()
        if not has_org_membership:
            logger.info(
                's3_permission_required_organization_membership_not_foundd',
                request={
                    'method': request.method,
                    'user': request.user,
                    'user_is_authenticated': request.user.is_authenticated,
                }
            )
        return has_org_membership


class S3BucketPermission(permissions.BasePermission):
    """Require organization membership in order to do anything with s3 Buckets."""

    def has_object_permission(self, request, view, obj):
        if not bool(request.user and request.user.is_authenticated):
            logger.info(
                's3_permission_user_missing_or_not_authenticated',
                request={
                    'method': request.method,
                    'user': request.user,
                    'user_is_authenticated': request.user.is_authenticated,
                }
            )
            return False

        has_org_membership = request.user in obj.organization.users.all()
        if not has_org_membership:
            logger.info(
                's3_permission_required_organization_membership_not_foundd',
                request={
                    'method': request.method,
                    'user': request.user,
                    'user_is_authenticated': request.user.is_authenticated,
                }
            )
        return has_org_membership

class SampleGroupPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads if the group is public
        if request.method in permissions.SAFE_METHODS and obj.is_public:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        return request.user.organization_set.filter(pk=obj.organization.pk).exists()


class SamplePermission(permissions.BasePermission):
    """Require organization membership in order to write to sample."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads on samples in public groups
        grp = obj.library.group
        if request.method in permissions.SAFE_METHODS and grp.is_public:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        organization = grp.organization
        return request.user.organization_set.filter(pk=organization.pk).exists()


class SampleAnalysisResultPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample analysis result."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads
        grp = obj.sample.library.group
        if request.method in permissions.SAFE_METHODS and grp.is_public:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        organization = grp.organization
        return request.user.organization_set.filter(pk=organization.pk).exists()


class SampleGroupAnalysisResultPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group analysis result."""

    def has_object_permission(self, request, view, obj):
        grp = obj.sample_group
        # Allow all reads if group is public
        if request.method in permissions.SAFE_METHODS and grp.is_public:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        organization = grp.organization
        return request.user.organization_set.filter(pk=organization.pk).exists()


class SampleAnalysisResultFieldPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample analysis result."""

    def has_object_permission(self, request, view, obj):
        grp = obj.analysis_result.sample.library.group
        # Allow all reads if group is public
        if request.method in permissions.SAFE_METHODS and grp.is_public:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        organization = grp.organization
        return request.user.organization_set.filter(pk=organization.pk).exists()


class SampleGroupAnalysisResultFieldPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group analysis result."""

    def has_object_permission(self, request, view, obj):
        grp = obj.analysis_result.sample_group
        # Allow all reads if group is public
        if request.method in permissions.SAFE_METHODS and grp.is_public:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        organization = grp.organization
        return request.user.organization_set.filter(pk=organization.pk).exists()


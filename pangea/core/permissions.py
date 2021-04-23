
import structlog
from rest_framework import permissions


logger = structlog.get_logger(__name__)


class PangeaUserPermission(permissions.BasePermission):
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

        # Require logged in user to BE this user to edit/delete
        if not request.user == obj:
            logger.info(
                'required_user_is_user_not_found',
                request={
                    'method': request.method,
                    'user': request.user,
                    'user_is_authenticated': request.user.is_authenticated,
                }
            )
            return False
        return True


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


class WorkOrderPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads if the group is public
        if not bool(request.user and request.user.is_authenticated):
            return False
        group = obj.sample.library.group
        return group.user_can_access(request.user)


class JobOrderPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads if the group is public
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            group = obj.work_order.sample.library.group
            return group.user_can_access(request.user)
        return obj.user_is_privileged(request.user)


class GroupWorkOrderPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads if the group is public
        if not bool(request.user and request.user.is_authenticated):
            return False
        group = obj.sample_group
        return group.user_can_access(request.user)


class ProjectPermission(permissions.BasePermission):
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


class SampleGroupPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads if the group is public
        if request.method in permissions.SAFE_METHODS and obj.is_public:
            return True

        return obj.user_can_access(request.user)


def sample_work_order_permissions(request, sample, work_order_uuid):
    work_order = sample.work_orders.filter(pk=work_order_uuid)
    if not work_order.exists():
        return False
    work_order = work_order.get()
    return work_order.user_is_privileged(request.user)


class SamplePermission(permissions.BasePermission):
    """Require organization membership in order to write to sample."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads on samples in public groups
        grp = obj.library.group
        if request.method in permissions.SAFE_METHODS and grp.is_public:
            return True

        work_order_uuid = request.query_params.get('work_order_uuid', None)
        if work_order_uuid:
            # if the client requests using a work order we require that they are a privileged user
            return sample_work_order_permissions(request, obj, work_order_uuid)

        # Require auth for write operations
        return obj.user_can_access(request.user)


class SampleAnalysisResultPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample analysis result."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads
        grp = obj.sample.library.group
        is_public = (not obj.is_private) and grp.is_public
        if request.method in permissions.SAFE_METHODS and is_public:
            return True

        work_order_uuid = request.query_params.get('work_order_uuid', None)
        if work_order_uuid:
            # if the client requests using a work order we require that they are a privileged user
            return sample_work_order_permissions(request, obj.sample, work_order_uuid)

        # Require auth for write operations
        return obj.user_can_access(request.user)


class SampleGroupAnalysisResultPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group analysis result."""

    def has_object_permission(self, request, view, obj):
        grp = obj.sample_group
        is_public = (not obj.is_private) and grp.is_public
        # Allow all reads if group is public
        if request.method in permissions.SAFE_METHODS and is_public:
            return True

        # Require auth for write operations
        return obj.user_can_access(request.user)


class SampleAnalysisResultFieldPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample analysis result."""

    def has_object_permission(self, request, view, obj):
        grp = obj.analysis_result.sample.library.group
        is_public = (not obj.analysis_result.is_private) and grp.is_public
        # Allow all reads if group is public
        if request.method in permissions.SAFE_METHODS and is_public:
            return True

        work_order_uuid = request.query_params.get('work_order_uuid', None)
        if work_order_uuid:
            # if the client requests using a work order we require that they are a privileged user
            return sample_work_order_permissions(request, obj.analysis_result.sample, work_order_uuid)

        # Require auth for write operations
        return obj.user_can_access(request.user)


class SampleGroupAnalysisResultFieldPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group analysis result."""

    def has_object_permission(self, request, view, obj):
        grp = obj.analysis_result.sample_group
        is_public = (not obj.analysis_result.is_private) and grp.is_public
        # Allow all reads if group is public
        if request.method in permissions.SAFE_METHODS and is_public:
            return True

        # Require auth for write operations
        return obj.user_can_access(request.user)

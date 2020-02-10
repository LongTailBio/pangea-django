from rest_framework import permissions


class OrganizationPermission(permissions.BasePermission):
    """Require organization membership in order to modify organization."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        return view.get_queryset().filter(users=request.user).exists()


class SampleGroupPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        return request.user.organization_set.filter(pk=obj.organization.pk).exists()


class SamplePermission(permissions.BasePermission):
    """Require organization membership in order to write to sample."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        return request.user.organization_set.filter(pk=obj.library.group.organization.pk).exists()


class SampleAnalysisResultPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample analysis result."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        organization = obj.sample.library.group.organization
        return request.user.organization_set.filter(pk=organization.pk).exists()


class SampleGroupAnalysisResultPermission(permissions.BasePermission):
    """Require organization membership in order to write to sample group analysis result."""

    def has_object_permission(self, request, view, obj):
        # Allow all reads
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require auth for write operations
        if not bool(request.user and request.user.is_authenticated):
            return False

        # Require organization membership to edit/delete
        organization = obj.sample_group.organization
        return request.user.organization_set.filter(pk=organization.pk).exists()

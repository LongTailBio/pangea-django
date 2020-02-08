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

        # Allow authenticated user to create an organization
        if request.method == 'POST':
            return True

        # Allow members of organization to edit/delete
        return view.get_queryset().filter(users=request.user).exists()

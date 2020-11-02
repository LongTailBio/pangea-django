import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .utils import PermissionedListCreateAPIView
from ..models import (
    SampleGroup,
    Project,
)
from ..permissions import (
    ProjectPermission,
)
from ..serializers import (
    SampleGroupSerializer,
    ProjectSerializer,
    ProjectAddSampleGroupSerializer
)


logger = structlog.get_logger(__name__)


class ProjectCreateView(PermissionedListCreateAPIView):
    queryset = Project.objects.all().order_by('created_at')
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'organization_id', 'name']
    permission = ProjectPermission

    def perform_create(self, serializer):
        """Require organization membership to create sample group."""
        organization = serializer.validated_data.get('organization')
        membership_queryset = self.request.user.organization_set.filter(pk=organization.pk)
        if not membership_queryset.exists():
            logger.warning(
                'attempted_create_project_without_permission',
                organization={'uuid': organization.pk, 'name': organization.name},
            )
            raise PermissionDenied(_('Organization membership is required to create a project.'))
        serializer.save()


class ProjectDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Project.objects.all().order_by('created_at')
    serializer_class = ProjectSerializer
    permission_classes = (ProjectPermission,)


class ProjectSampleGroupsView(generics.ListAPIView):
    """This class handles managing membership of sample groups within projects."""
    permission_classes = (ProjectPermission,)
    queryset = SampleGroup.objects.all().order_by('created_at')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SampleGroupSerializer
        if self.request.method == 'POST':
            return ProjectAddSampleGroupSerializer

    def filter_queryset(self, queryset):
        proj_uuid = self.kwargs.get('project_pk')
        project = Project.objects.get(pk=proj_uuid)
        perm = ProjectPermission()
        has_permission = perm.has_object_permission(self.request, self, project)
        if not has_permission:
            return []
        return project.sample_groups.order_by('created_at')

    def post(self, request, *args, **kwargs):
        project = Project.objects.get(pk=kwargs.get('project_pk'))
        group = SampleGroup.objects.get(pk=request.data.get('sample_group_uuid'))
        group_member_query = self.request.user.organization_set.filter(pk=group.organization.pk)
        proj_member_query = self.request.user.organization_set.filter(pk=project.organization.pk)

        if not group_member_query.exists() or not proj_member_query.exists():
            logger.info(
                'attempted_add_sample_group_to_project_without_permission',
                user=request.user,
                project_pk=project.pk,
                sample_group_pk=group.pk,
            )
            raise PermissionDenied(_('Insufficient permissions to add sample group to project.'))
        project.add_sample_group(group)
        return Response({"status": "success"})

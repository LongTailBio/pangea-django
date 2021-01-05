import structlog
from random import shuffle
import json

from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response

from uuid import UUID
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import api_view, authentication_classes

from pangea.core.views.utils import PermissionedListCreateAPIView
from pangea.core.param_auth import TokenParamAuthentication
from .models import (
    Tag,
    SampleGroup,
    Sample,
)
from pangea.core.permissions import (
    SampleGroupPermission,
    SamplePermission,
)
from .serializers import (
    TagSerializer,
    TagAddTagSerializer,
    TagAddSampleGroupSerializer,
    TagAddSampleSerializer,
)
from pangea.core.serializers import (
    SampleGroupSerializer,
    SampleSerializer,
)


logger = structlog.get_logger(__name__)


def is_uuid(el):
    """Return true if el is an UUID."""
    try:
        UUID(el)
        return True
    except ValueError:
        return False


class TagCreateView(generics.ListCreateAPIView):
    queryset = Tag.objects.all().order_by('created_at')
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'name']

    def get_queryset(self):
        sample_pk = self.request.query_params.get('sample', None)
        qset = self.queryset
        if sample_pk:
            qset = qset.filter(tagged_samples__sample__uuid__contains=sample_pk)
        return qset


class TagDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Tag.objects.all().order_by('created_at')
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)


class TagNameDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Tag.objects.all().order_by('created_at')
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    lookup_field = 'name'


class TagTagsView(generics.ListAPIView):
    """This class handles managing membership of sample groups within projects."""
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Tag.objects.all().order_by('created_at')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TagSerializer
        if self.request.method == 'POST':
            return TagAddTagSerializer

    def post(self, request, *args, **kwargs):
        tag = Tag.objects.get(pk=kwargs.get('tag_pk'))
        other_tag = Tag.objects.get(pk=request.data.get('tag_uuid'))
        payload = request.data.get('payload', '')
        tag.add_related_tag(other_tag, payload=payload)
        return Response({"status": "success"})


class TagSampleGroupsView(generics.ListAPIView):
    """This class handles tagging sample groups."""
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = SampleGroup.objects.all().order_by('created_at')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SampleGroupSerializer
        if self.request.method == 'POST':
            return TagAddSampleGroupSerializer

    def filter_queryset(self, queryset):
        tag = Tag.objects.get(pk=self.kwargs.get('tag_pk'))
        perm = SampleGroupPermission()
        sample_groups = [
            grp.sample_group
            for grp in tag.tagged_sample_groups.order_by('created_at')
            if perm.has_object_permission(self.request, self, grp.sample_group)
        ]
        return sample_groups

    def post(self, request, *args, **kwargs):
        tag = Tag.objects.get(pk=kwargs.get('tag_pk'))
        group = SampleGroup.objects.get(pk=request.data.get('sample_group_uuid'))
        group_member_query = self.request.user.organization_set.filter(pk=group.organization.pk)

        if not group.is_public and not group_member_query.exists():
            logger.info(
                'attempted_tag_sample_group_without_permission',
                user=request.user,
                tag_pk=tag.pk,
                sample_group_pk=group.pk,
            )
            raise PermissionDenied(_('Insufficient permissions to tag sample group.'))
        tag.tag_sample_group(group)
        return Response({"status": "success"})


class TagSamplesView(generics.ListAPIView):
    """This class handles tagging samples."""
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Sample.objects.all().order_by('created_at')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SampleSerializer
        if self.request.method == 'POST':
            return TagAddSampleSerializer

    def filter_queryset(self, queryset):
        tag = Tag.objects.get(pk=self.kwargs.get('tag_pk'))
        perm = SamplePermission()
        samples = (
            sample_rel.sample
            for sample_rel in tag.tagged_samples.all()
        )
        samples = [
            sample for sample in samples
            if perm.has_object_permission(self.request, self, sample)
        ]
        return samples

    def post(self, request, *args, **kwargs):
        tag = Tag.objects.get(pk=kwargs.get('tag_pk'))
        sample = Sample.objects.get(pk=request.data.get('sample_uuid'))
        sample_member_query = self.request.user.organization_set.filter(pk=sample.organization.pk)

        if not sample.is_public and not sample_member_query.exists():
            logger.info(
                'attempted_tag_sample_without_permission',
                user=request.user,
                tag_pk=tag.pk,
                sample_pk=sample.pk,
            )
            raise PermissionDenied(_('Insufficient permissions to tag sample.'))
        tag.tag_sample(sample)
        return Response({"status": "success"})


@api_view(['GET'])
def get_random_samples_in_tag(request, tag_pk):
    """Reply with metadata for samples in group."""
    tag = Tag.objects.get(pk=tag_pk)
    perm = SamplePermission()
    samples = [
        sample_rel.sample
        for sample_rel in tag.tagged_samples.all()
    ]
    shuffle(samples)
    n_samples = int(request.GET.get('n', 100))
    samples = samples[:n_samples]
    perm = SamplePermission()
    samples = [
        sample for sample in samples
        if perm.has_object_permission(request, None, sample)
    ]
    samples = [SampleSerializer(sample).data for sample in samples]
    return Response({'results': samples})


@api_view(['GET'])
@authentication_classes([TokenParamAuthentication])
def get_sample_ar_counts_in_tag(request, pk):
    """Reply with counts for all types of sample analysis results in the group."""
    tag = Tag.objects.get(pk=pk)
    perm = SamplePermission()
    blob = {'n_samples': 0}
    for sample in tag.tagged_samples.all():
        if not perm.has_object_permission(request, None, sample):
            continue
        blob['n_samples'] += 1
        for module_name in {ar.module_name for ar in sample.analysis_result_set.all()}:
            blob[module_name] = 1 + blob.get(module_name, 0)

    return Response(blob)


@api_view(['GET'])
@authentication_classes([TokenParamAuthentication])
def get_sample_group_ar_counts_in_tag(request, pk):
    """Reply with counts for all types of sample analysis results in the group."""
    tag = Tag.objects.get(pk=pk)
    perm = SampleGroupPermission()
    blob = {'n_groups': 0}
    for group in tag.tagged_sample_groups.all():
        if not perm.has_object_permission(request, None, group):
            continue
        blob['n_groups'] += 1
        for module_name in {ar.module_name for ar in group.analysis_result_set.all()}:
            blob[module_name] = 1 + blob.get(module_name, 0)

    return Response(blob)

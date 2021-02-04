import structlog

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import generics
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from ..models import (
    Pipeline,
    PipelineModule,
)
from ..serializers import (
    PipelineSerializer,
    PipelineModuleSerializer,
)


logger = structlog.get_logger(__name__)


class PipelineCreateView(generics.ListCreateAPIView):
    queryset = Pipeline.objects.all().order_by('created_at')
    serializer_class = PipelineSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'name']


class PipelineDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)


class PipelineNameDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    lookup_field = 'name'


@api_view(['GET'])
def get_module_in_pipeline(request, pk, name, version):
    """Reply with counts for all types of sample analysis results in the group."""
    try:
        pipeline = Pipeline.objects.get(pk=pk)
    except:  # TODO broad except
        raise ObjectDoesNotExist(_(f'Pipeline with uuid {pk} not found'))
    try:
        pm = PipelineModule.objects.get(pipeline=pipeline, name=name, version=version)
    except:  # TODO broad except
        raise ObjectDoesNotExist(_(f'PipelineModule with name {name} and version {version} not found in pipeline {pipeline.name}'))
    blob = PipelineModuleSerializer(pm).data
    return Response(blob)


class PipelineModuleCreateView(generics.ListCreateAPIView):
    queryset = PipelineModule.objects.all().order_by('created_at')
    serializer_class = PipelineModuleSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'name']


class PipelineModuleDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = PipelineModule.objects.all()
    serializer_class = PipelineModuleSerializer

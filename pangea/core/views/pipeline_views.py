import structlog

from django.utils.translation import gettext_lazy as _

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


class PipelineModuleCreateView(generics.ListCreateAPIView):
    queryset = PipelineModule.objects.all().order_by('created_at')
    serializer_class = PipelineModuleSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_fields = ['uuid', 'name']


class PipelineModuleDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = PipelineModule.objects.all()
    serializer_class = PipelineModuleSerializer

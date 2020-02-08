from rest_framework import generics

from .models import (
    Organization,
    SampleGroup,
    Sample,
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
)
from .permissions import (
    OrganizationPermission,
)
from .serializers import (
    OrganizationSerializer,
    SampleGroupSerializer,
    SampleSerializer,
    SampleAnalysisResultSerializer,
    SampleGroupAnalysisResultSerializer,
)


class OrganizationCreateView(generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (OrganizationPermission,)

    def perform_create(self, serializer):
        organization = serializer.save()
        self.request.user.organization_set.add(organization)


class OrganizationDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (OrganizationPermission,)


class SampleGroupCreateView(generics.ListCreateAPIView):
    queryset = SampleGroup.objects.all()
    serializer_class = SampleGroupSerializer

    def perform_create(self, serializer):
        serializer.save()


class SampleGroupDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = SampleGroup.objects.all()
    serializer_class = SampleGroupSerializer


class SampleCreateView(generics.ListCreateAPIView):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer

    def perform_create(self, serializer):
        serializer.save()


class SampleDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer


class SampleAnalysisResultDetailsView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SampleAnalysisResult.objects.all()
    serializer_class = SampleAnalysisResultSerializer


class SampleGroupAnalysisResultDetailsView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SampleGroupAnalysisResult.objects.all()
    serializer_class = SampleGroupAnalysisResultSerializer

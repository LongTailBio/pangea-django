from rest_framework import generics

from .models import Organization
from .serializers import OrganizationSerializer


class OrganizationCreateView(generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def perform_create(self, serializer):
        serializer.save()


class OrganizationDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


# TODO: add views for remaining models

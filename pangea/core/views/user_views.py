import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import api_view

from ..models import (
    PangeaUser,
)
from ..permissions import (
    PangeaUserPermission,
)
from ..serializers import (
    PangeaUserSerializer,
)


logger = structlog.get_logger(__name__)


class PangeaUserListView(generics.ListAPIView):
    queryset = PangeaUser.objects.all()
    serializer_class = PangeaUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)


class PangeaUserDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    lookup_field = 'uuid'  # NB: NOT the PK on PangeaUser objects.
    queryset = PangeaUser.objects.all()
    serializer_class = PangeaUserSerializer
    permission_classes = (PangeaUserPermission,)


@api_view(['GET'])
def get_user_detail_by_djoser_id(request, user_id):
    """Reply with a PangeaUser."""
    user = PangeaUser.objects.get(id=user_id)
    blob = PangeaUserSerializer(user).data
    return Response(blob)
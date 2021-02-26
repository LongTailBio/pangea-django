import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

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


class PangeaUserDetailsView(generics.RetrieveUpdateDestroyAPIView):
    """This class handles the http GET, PUT and DELETE requests."""
    lookup_field = 'uuid'  # NB: NOT the PK on PangeaUser objects.
    queryset = PangeaUser.objects.all()
    serializer_class = PangeaUserSerializer
    permission_classes = (PangeaUserPermission,)

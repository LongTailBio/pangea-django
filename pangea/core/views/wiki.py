import structlog

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .utils import PermissionedListCreateAPIView
from ..models import (
    Wiki,
    WikiPage,
    SiteWiki,
    SampleGroupWiki,
    SampleGroup,
)
from ..permissions import (
    SampleGroupPermission,
)
from ..serializers import (
    WikiSerializer,
    WikiPageSerializer,
    SampleGroupWikiSerializer,
)


logger = structlog.get_logger(__name__)


@api_view(['POST', 'GET'])
def handle_sample_group_wiki(request, pk):
    if request.method == 'POST':
        return create_sample_group_wiki(request, pk)
    elif request.method == 'GET':
        return get_sample_group_wiki(request, pk)


def create_sample_group_wiki(request, pk):
    """"""
    grp = SampleGroup.objects.get(pk=pk)
    if not grp.user_can_access(request.user):
        raise PermissionDenied(_('Insufficient permissions to create wiki.'))
    if not hasattr(grp, 'wiki'):
        SampleGroupWiki.create_wiki(grp, request.data['title'], request.data['text'])
    elif request.data.get('uuid', None):
        grp.wiki.modify_page(request.data['uuid'], request.data['title'], request.data['text'])
    else:
        grp.wiki.add_page(request.data['title'], request.data['text'])
    return Response(WikiSerializer(grp.wiki).data, status=201)


def get_sample_group_wiki(request, pk):
    """"""
    grp = SampleGroup.objects.get(pk=pk)
    if not grp.user_can_access(request.user):
        raise PermissionDenied(_('Insufficient permissions to get wiki.'))
    status = 200
    if not hasattr(grp, 'wiki'):
        SampleGroupWiki.create_wiki(grp, 'Home Page', f'Wiki for Sample Group {grp.name}')
        status = 201
    return Response(WikiSerializer(grp.wiki).data, status=status)

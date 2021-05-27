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
    OrganizationWiki,
    PipelineWiki,
    SampleGroup,
    Organization,
    Pipeline,
    SiteAdmin,
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


def edit_wiki(request, pk):
    """"""
    wiki = Wiki.objects.get(pk=pk)
    if request.data.get('uuid', None):
        wiki.modify_page(request.data['uuid'], request.data['title'], request.data['text'])
    else:
        wiki.add_page(request.data['title'], request.data['text'])
    return Response(WikiSerializer(wiki).data, status=201)


@api_view(['GET', 'POST'])
def handle_sample_group_wiki(request, pk):
    """"""
    grp = SampleGroup.objects.get(pk=pk)
    if not grp.user_can_view(request.user):
        raise PermissionDenied(_('Insufficient permissions to view wiki.'))
    if request.method == 'POST':
        if not grp.user_can_access(request.user):
            raise PermissionDenied(_('Insufficient permissions to edit wiki.'))
        return edit_wiki(request, grp.wiki.wiki.uuid)
    status = 200
    if not hasattr(grp, 'wiki'):
        SampleGroupWiki.create_wiki(grp, 'Home Page', f'Wiki for Sample Group {grp.name}')
        status = 201
    return Response(WikiSerializer(grp.wiki).data, status=status)


@api_view(['GET', 'POST'])
def handle_organization_wiki(request, pk):
    """"""
    org = Organization.objects.get(pk=pk)
    if not org.user_can_view(request.user):
        raise PermissionDenied(_('Insufficient permissions to view wiki.'))
    if request.method == 'POST':
        if not org.user_can_access(request.user):
            raise PermissionDenied(_('Insufficient permissions to edit wiki.'))
        return edit_wiki(request, org.wiki.wiki.uuid)
    status = 200
    if not hasattr(org, 'wiki'):
        OrganizationWiki.create_wiki(org, 'Home Page', f'Wiki for Organization {org.name}')
        status = 201
    return Response(WikiSerializer(org.wiki).data, status=status)


@api_view(['GET', 'POST'])
def handle_pipeline_wiki(request, pk):
    """"""
    pipe = Pipeline.objects.get(pk=pk)
    if request.method == 'POST':
        return edit_wiki(request, pipe.wiki.wiki.uuid)
    status = 200
    if not hasattr(pipe, 'wiki'):
        PipelineWiki.create_wiki(pipe, 'Home Page', f'Wiki for Pipeline {pipe.name}')
        status = 201
    return Response(WikiSerializer(pipe.wiki).data, status=status)


@api_view(['GET', 'POST'])
def handle_site_wiki(request, pk):
    """"""
    if not SiteWiki.objects.exists():
        SiteWiki.create_wiki()
    wiki = SiteWiki.objects.get(0)
    if request.method == 'POST':
        if not SiteAdmin.object.filter(user == request.user).exists():
            raise PermissionDenied(_('Insufficient permissions to edit wiki.'))
        return edit_wiki(request, wiki.wiki.uuid)
    return Response(WikiSerializer(wiki).data, status=status)



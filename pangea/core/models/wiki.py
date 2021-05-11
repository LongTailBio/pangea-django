
from django.db import models

import uuid
import structlog

from pangea.core.mixins import AutoCreatedUpdatedMixin

from .sample_group import SampleGroup


logger = structlog.get_logger(__name__)


class WikiPage(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField(blank=False, unique=True)
    text = models.TextField(blank=True, default='')
    wiki = models.ForeignKey('Wiki', on_delete=models.CASCADE, related_name='pages')

    def __str__(self):
        return f'<WikiPage title="{self.title}" uuid={self.uuid}/>'


class Wiki(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    home_page = models.OneToOneField('WikiPage', on_delete=models.CASCADE, related_name='home_wiki', null=True)
    sidebar = models.OneToOneField('WikiPage', on_delete=models.CASCADE, related_name='sidebar_wiki', null=True)

    def add_page(self, title, text):
        page = WikiPage.objects.create(
            wiki=self,
            title=title,
            text=text,
        )
        return page

    def modify_page(self, uuid, title, text):
        page = self.pages.get(pk=uuid)
        page.title = title
        page.text = text
        page.save()
        return page

    @classmethod
    def create_with_home_page(cls, title, text):
        wiki = cls.objects.create()
        home_page = WikiPage.objects.create(
            wiki=wiki,
            title=title,
            text=text,
        )
        wiki.home_page = home_page
        wiki.save()
        return wiki


class ObjectWiki(AutoCreatedUpdatedMixin):
    wiki = models.OneToOneField('Wiki', on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def add_page(self, title, text):
        return self.wiki.add_page(title, text)

    def modify_page(self, uuid, title, text):
        return self.wiki.modify_page(uuid, title, text)


class SiteWiki(ObjectWiki):
    pass


class SampleGroupWiki(ObjectWiki):
    sample_group = models.OneToOneField('SampleGroup', on_delete=models.CASCADE, related_name='wiki', primary_key=True)
    wiki = models.OneToOneField('Wiki', on_delete=models.CASCADE)

    @property
    def pages(self):
        return self.wiki.pages

    @property
    def home_page(self):
        return self.wiki.home_page

    @property
    def sidebar(self):
        return self.wiki.sidebar

    @classmethod
    def create_wiki(cls, grp, title='', text=''):
        wiki = Wiki.create_with_home_page(title, text)
        grp_wiki = cls.objects.create(sample_group=grp, wiki=wiki)
        return grp_wiki

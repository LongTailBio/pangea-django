from rest_framework import serializers
from django.db.models import Q
import structlog

from ..models import (
	WikiPage,
	Wiki,
	SiteWiki,
	SampleGroupWiki,
)


class WikiPageSerializer(serializers.ModelSerializer):

    class Meta:
        model = WikiPage
        fields = (
            'uuid', 'title', 'created_at', 'updated_at',
            'text', 'wiki',
        )
        read_only_fields = ('created_at', 'updated_at',)



class WikiSerializer(serializers.ModelSerializer):
    home_page_obj = WikiPageSerializer(source='home_page', read_only=True)
    sidebar_obj = WikiPageSerializer(source='sidebar', read_only=True)
    page_objs = serializers.SerializerMethodField()

    class Meta:
        model = Wiki
        fields = (
            'uuid', 'pages',
            'created_at', 'updated_at', 'page_objs', 'home_page_obj', 'sidebar_obj',
        )
        read_only_fields = (
        	'created_at', 'updated_at',
        	'home_page_obj', 'sidebar_obj',
        )

    def get_page_objs(self, obj):
        return [
            WikiPageSerializer(page).data
            for page in obj.pages.all()
        ]


class SampleGroupWikiSerializer(serializers.ModelSerializer):
    wiki_obj = WikiSerializer(source='wiki', read_only=True)

    class Meta:
        model = SampleGroupWiki
        fields = (
            'sample_group', 'wiki', 'created_at', 'updated_at', 'wiki_obj'
        )
        read_only_fields = (
        	'created_at', 'updated_at', 'wiki_obj',
        )

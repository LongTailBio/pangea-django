
from rest_framework import serializers

from .models import (
    Tag,
)

class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('uuid', 'name', 'created_at', 'updated_at', 'payload')


class TagAddTagSerializer(serializers.Serializer):
    tag_uuid = serializers.UUIDField()


class TagAddSampleGroupSerializer(serializers.Serializer):
    sample_group_uuid = serializers.UUIDField()


class TagAddSampleSerializer(serializers.Serializer):
    sample_uuid = serializers.UUIDField()

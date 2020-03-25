from rest_framework import serializers

from pangea.core.models import PangeaUser


class Covid19ReadsUploadSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=PangeaUser.objects.all())
    raw_reads_path = serializers.URLField()

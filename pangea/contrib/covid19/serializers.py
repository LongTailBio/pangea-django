from rest_framework import serializers

from pangea.core.models import Sample


class Covid19ReadsUploadSerializer(serializers.Serializer):
    sample = serializers.PrimaryKeyRelatedField(queryset=Sample.objects.all())
    raw_reads = serializers.FileField()

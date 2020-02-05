from rest_framework import serializers

from .models import Organization


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = ('uuid', 'name', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


# TODO: add remaining models

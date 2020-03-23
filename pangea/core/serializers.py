from rest_framework import serializers

from .models import (
    PangeaUser,
    Organization,
    SampleGroup,
    Sample,
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
)


class PangeaUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = PangeaUser
        fields = ('email', 'is_staff', 'is_active', 'personal_org_uuid')
        read_only_fields = ('email', 'personal_org_uuid')


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = ('uuid', 'name', 'created_at', 'updated_at', 'core_sample_group_uuid')
        read_only_fields = ('created_at', 'updated_at', 'core_sample_group_uuid')


class OrganizationAddUserSerializer(serializers.Serializer):
    user_uuid = serializers.UUIDField()


class SampleGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleGroup
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'organization', 'description', 'is_library',
            'is_public', 'theme'
        )
        read_only_fields = ('created_at', 'updated_at')


class SampleGroupAddSampleSerializer(serializers.Serializer):
    sample_uuid = serializers.UUIDField()


class SampleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sample
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'library', 'metadata',
        )
        read_only_fields = ('created_at', 'updated_at')


class SampleAnalysisResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample', 'created_at', 'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class SampleGroupAnalysisResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleGroupAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample_group', 'created_at', 'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class SampleAnalysisResultFieldSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleAnalysisResultField
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'stored_data', 'analysis_result',
        )
        read_only_fields = ('created_at', 'updated_at')


class SampleGroupAnalysisResultFieldSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleGroupAnalysisResultField
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'stored_data', 'analysis_result',
        )
        read_only_fields = ('created_at', 'updated_at')

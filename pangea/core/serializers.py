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
        fields = ('email', 'is_staff', 'is_active')
        read_only_fields = ('email',)


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = ('uuid', 'name', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class SampleGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleGroup
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'organization', 'description', 'is_library',
            'is_public', 'theme'
        )
        read_only_fields = ('created_at', 'updated_at')


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
            'uuid', 'name', 'created_at', 'updated_at',
            'module_name', 'replicate', 'sample',
        )
        read_only_fields = ('created_at', 'updated_at')


class SampleGroupAnalysisResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleGroupAnalysisResult
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'module_name', 'replicate', 'sample_group',
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

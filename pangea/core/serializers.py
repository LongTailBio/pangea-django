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
    user = serializers.PrimaryKeyRelatedField(queryset=PangeaUser.objects.all())


class SampleGroupSerializer(serializers.ModelSerializer):

    organization_obj = OrganizationSerializer(source='organization')

    class Meta:
        model = SampleGroup
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'organization', 'description', 'is_library',
            'is_public', 'theme', 'organization_obj'
        )
        read_only_fields = ('created_at', 'updated_at', 'organization_obj')


class SampleGroupAddSampleSerializer(serializers.Serializer):
    sample_uuid = serializers.UUIDField()


class SampleSerializer(serializers.ModelSerializer):

    library_obj = SampleGroupSerializer(source='library.group')

    class Meta:
        model = Sample
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'library', 'metadata', 'library_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'library_obj')


class SampleAnalysisResultSerializer(serializers.ModelSerializer):

    sample_obj = SampleSerializer(source='sample')

    class Meta:
        model = SampleAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample', 'created_at', 'updated_at',
            'sample_obj'
        )
        read_only_fields = ('created_at', 'updated_at', 'sample_obj')


class SampleGroupAnalysisResultSerializer(serializers.ModelSerializer):

    sample_group_obj = SampleGroupSerializer(source='sample_group')

    class Meta:
        model = SampleGroupAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample_group', 'created_at', 'updated_at',
            'sample_group_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'sample_group_obj')


class SampleAnalysisResultFieldSerializer(serializers.ModelSerializer):

    analysis_result_obj = SampleAnalysisResultSerializer(source='analysis_result')

    class Meta:
        model = SampleAnalysisResultField
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'stored_data', 'analysis_result',
            'analysis_result_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'analysis_result_obj')


class SampleGroupAnalysisResultFieldSerializer(serializers.ModelSerializer):

    analysis_result_obj = SampleGroupAnalysisResultSerializer(source='analysis_result')

    class Meta:
        model = SampleGroupAnalysisResultField
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'stored_data', 'analysis_result',
            'analysis_result_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'analysis_result_obj')

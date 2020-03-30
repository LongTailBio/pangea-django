
from rest_framework import serializers
from django.db.models import Q

from .models import (
    PangeaUser,
    Organization,
    S3ApiKey,
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


class S3ApiKeySerializer(serializers.ModelSerializer):

    class Meta:
        model = S3ApiKey
        fields = (
            'uuid', 'description', 'created_at', 'updated_at',
            'endpoint_url', 'bucket', 'public_key', 'private_key',
            'organization',
        )
        read_only_fields = ('created_at', 'updated_at', 'uuid')
        extra_kwargs = {
            'private_key': {'write_only': True}
        }


class OrganizationAddUserSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=PangeaUser.objects.all())


class SampleGroupSerializer(serializers.ModelSerializer):

    organization_obj = OrganizationSerializer(source='organization', read_only=True)

    class Meta:
        model = SampleGroup
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'organization', 'description', 'is_library',
            'is_public', 'theme', 'organization_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'organization_obj')


class SampleGroupAddSampleSerializer(serializers.Serializer):
    sample_uuid = serializers.UUIDField()


class SampleSerializer(serializers.ModelSerializer):

    library_obj = SampleGroupSerializer(source='library.group', read_only=True)

    class Meta:
        model = Sample
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'library', 'metadata', 'library_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'library_obj')


class SampleAnalysisResultSerializer(serializers.ModelSerializer):

    sample_obj = SampleSerializer(source='sample', read_only=True)

    class Meta:
        model = SampleAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample', 'created_at', 'updated_at',
            'sample_obj'
        )
        read_only_fields = ('created_at', 'updated_at', 'sample_obj')


class SampleGroupAnalysisResultSerializer(serializers.ModelSerializer):

    sample_group_obj = SampleGroupSerializer(source='sample_group', read_only=True)

    class Meta:
        model = SampleGroupAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample_group', 'created_at', 'updated_at',
            'sample_group_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'sample_group_obj')


def presign_ar_field_stored_data_if_appropriate(ret, org):
    """Intercept serialization of an analysis result field to add a presigned URL.

    At this point we are assuming the user has permission to access this result.
    """
    if ret['stored_data'].get('__type__', '').lower() != 's3':
        return ret
    bucket_name = ret['stored_data']['uri'].split('s3://')[1].split('/')[0]
    s3key_query = org.s3_api_keys \
        .filter(endpoint_url=ret['stored_data']['endpoint_url']) \
        .filter(Q(bucket='*') | Q(bucket=bucket_name))
    if s3key_query.exists():
        s3key = s3key_query[0]
        ret['stored_data']['presigned_url'] = s3key.presign_url(
            ret['stored_data']['endpoint_url'],
            ret['stored_data']['uri']
        )
    return ret


class SampleAnalysisResultFieldSerializer(serializers.ModelSerializer):

    analysis_result_obj = SampleAnalysisResultSerializer(source='analysis_result', read_only=True)

    class Meta:
        model = SampleAnalysisResultField
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'stored_data', 'analysis_result',
            'analysis_result_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'analysis_result_obj')

    def to_representation(self, instance):
        """Convert `username` to lowercase."""
        ret = super().to_representation(instance)
        return presign_ar_field_stored_data_if_appropriate(
            ret,
            instance.analysis_result.sample.library.group.organization,
        )


class SampleGroupAnalysisResultFieldSerializer(serializers.ModelSerializer):

    analysis_result_obj = SampleGroupAnalysisResultSerializer(source='analysis_result',
                                                              read_only=True)

    class Meta:
        model = SampleGroupAnalysisResultField
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'stored_data', 'analysis_result',
            'analysis_result_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'analysis_result_obj')

    def to_representation(self, instance):
        """Convert `username` to lowercase."""
        ret = super().to_representation(instance)
        return presign_ar_field_stored_data_if_appropriate(
            ret,
            instance.analysis_result.group.organization,
        )

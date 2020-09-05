
from rest_framework import serializers
from django.db.models import Q
import structlog

from .models import (
    PangeaUser,
    Organization,
    S3ApiKey,
    S3Bucket,
    SampleGroup,
    Sample,
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
    Project,
)

logger = structlog.get_logger(__name__)


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


class S3BucketSerializer(serializers.ModelSerializer):

    class Meta:
        model = S3Bucket
        fields = (
            'uuid', 'name', 'endpoint_url', 'organization',
        )


class S3ApiKeySerializer(serializers.ModelSerializer):

    class Meta:
        model = S3ApiKey
        fields = (
            'uuid', 'description', 'created_at', 'updated_at',
            'bucket', 'public_key', 'private_key',
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
            'long_description'
        )
        read_only_fields = ('created_at', 'updated_at', 'organization_obj')


class SampleGroupAddSampleSerializer(serializers.Serializer):
    sample_uuid = serializers.UUIDField()


class ProjectSerializer(serializers.ModelSerializer):

    organization_obj = OrganizationSerializer(source='organization', read_only=True)

    class Meta:
        model = Project
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'organization', 'description', 'organization_obj',
            'sample_groups', 'sub_projects',
        )
        read_only_fields = ('created_at', 'updated_at', 'organization_obj')


class ProjectAddSampleGroupSerializer(serializers.Serializer):
    sample_group_uuid = serializers.UUIDField()


class SampleSerializer(serializers.ModelSerializer):

    library_obj = SampleGroupSerializer(source='library.group', read_only=True)

    class Meta:
        model = Sample
        fields = (
            'uuid', 'name', 'created_at', 'updated_at',
            'library', 'metadata', 'library_obj', 'description'
        )
        read_only_fields = ('created_at', 'updated_at', 'library_obj')


class SampleAnalysisResultSerializer(serializers.ModelSerializer):

    sample_obj = SampleSerializer(source='sample', read_only=True)

    class Meta:
        model = SampleAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample', 'created_at', 'updated_at',
            'sample_obj', 'description', 'metadata',
        )
        read_only_fields = ('created_at', 'updated_at', 'sample_obj')


class SampleGroupAnalysisResultSerializer(serializers.ModelSerializer):

    sample_group_obj = SampleGroupSerializer(source='sample_group', read_only=True)

    class Meta:
        model = SampleGroupAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample_group', 'created_at', 'updated_at',
            'sample_group_obj', 'description', 'metadata',
        )
        read_only_fields = ('created_at', 'updated_at', 'sample_group_obj')


def presign_ar_field_stored_data_if_appropriate(ret, grp):
    """Intercept serialization of an analysis result field to add a presigned URL.

    At this point we are assuming the user has permission to access this result.
    """
    try:
        return _presign_ar_field_stored_data_if_appropriate(ret, grp)
    except Exception as e:
        # Gracefully fail here. Presigning fail isn't a reason to fail to respond
        logger.error(
            'presigning_url_failed_during_serialization',
            grp_uuid=grp.uuid,
            stored_data=ret,
            exception=str(e),
        )
        return ret


def _presign_ar_field_stored_data_if_appropriate(ret, grp):
    if ret['stored_data'].get('__type__', '').lower() != 's3':
        return ret
    if not grp.bucket:
        #assert False
        return ret
    if not grp.bucket.api_key:
        assert False
        return ret
    ret['stored_data']['presigned_url'] = grp.bucket.api_key.presign_url(
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
            instance.analysis_result.sample.library.group,
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
            instance.analysis_result.sample_group,
        )

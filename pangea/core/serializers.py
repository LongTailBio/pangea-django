
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
    Pipeline,
    PipelineModule,
    JobOrder,
    WorkOrder,
    JobOrderProto,
    WorkOrderProto
)

logger = structlog.get_logger(__name__)


class PangeaUserSerializer(serializers.ModelSerializer):

    organization_objs = serializers.SerializerMethodField()
    saved_sample_group_objs = serializers.SerializerMethodField()

    class Meta:
        model = PangeaUser
        fields = (
            'id', 'uuid', 'email', 'is_staff', 'is_active',
            'personal_org_uuid', 'organization_objs',
            'saved_sample_group_objs',

            'avatar', 'name', 'biography', 'url',
            'twitter_username', 'github_username',
            'company', 'location',
        )
        read_only_fields = ('email', 'personal_org_uuid')

    def get_organization_objs(self, obj):
        return [
            {'uuid': org.uuid, 'name': org.name}
            for org in obj.organization_set.all()
        ]

    def get_saved_sample_group_objs(self, obj):
        return [
            {'uuid': grp.uuid, 'name': grp.name}
            for grp in obj.saved_sample_groups.all()
        ]


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
            'long_description', 'metadata', 'bucket',
            'storage_provider_name',
        )
        read_only_fields = ('created_at', 'updated_at', 'organization_obj')


class SampleGroupAddSampleSerializer(serializers.Serializer):
    sample_uuid = serializers.UUIDField()


class PipelineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Pipeline
        fields = (
            'uuid', 'name', 'description', 'long_description',
            'updated_at', 'created_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class PipelineModuleSerializer(serializers.ModelSerializer):

    pipeline_obj = PipelineSerializer(source='pipeline', read_only=True)
    dependency_modules = serializers.SerializerMethodField()
    downstream_modules = serializers.SerializerMethodField()

    class Meta:
        model = PipelineModule
        fields = (
            'uuid', 'name', 'version', 'description', 'long_description',
            'updated_at', 'created_at', 'metadata', 'pipeline', 'pipeline_obj',
            'dependencies', 'dependency_modules', 'downstream_modules',
        )
        read_only_fields = ('created_at', 'updated_at', 'pipeline_obj')

    def get_dependency_modules(self, obj):
        return [
            [depends.uuid, depends.name, depends.version]
            for depends in obj.dependencies.all()
        ]

    def get_downstream_modules(self, obj):
        return [
            [downstream.uuid, downstream.name, downstream.version]
            for downstream in obj.downstreams.all()
        ]


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
            'library', 'metadata', 'library_obj', 'description',
        )
        read_only_fields = ('created_at', 'updated_at', 'library_obj',)

    def update(self, sample, validated_data):
        """Update the sample model

        slight modification of the default update method
        https://github.com/encode/django-rest-framework/blob/3db88778893579e1d7609b584ef35409c8aa5a22/rest_framework/serializers.py#L968
        """
        old_library = sample.library
        super().update(sample, validated_data)
        new_library = sample.library
        if old_library != new_library:
            old_library.group.sample_set.remove(sample)
            new_library.group.add_sample(sample)
        if 'metadata' in self.initial_data:
            sample.metadata = self.initial_data['metadata']
            sample.save()
        return sample


class SampleAnalysisResultSerializer(serializers.ModelSerializer):

    sample_obj = SampleSerializer(source='sample', read_only=True)
    pipeline_module_obj = PipelineModuleSerializer(source='pipeline_module', read_only=True)

    class Meta:
        model = SampleAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample', 'created_at', 'updated_at',
            'sample_obj', 'description', 'metadata',
            'is_private', 'pipeline_module', 'pipeline_module_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'sample_obj', 'pipeline_module_obj')


class SampleGroupAnalysisResultSerializer(serializers.ModelSerializer):

    sample_group_obj = SampleGroupSerializer(source='sample_group', read_only=True)
    pipeline_module_obj = PipelineModuleSerializer(source='pipeline_module', read_only=True)

    class Meta:
        model = SampleGroupAnalysisResult
        fields = (
            'uuid', 'module_name', 'replicate',
            'sample_group', 'created_at', 'updated_at',
            'sample_group_obj', 'description', 'metadata',
            'is_private', 'pipeline_module', 'pipeline_module_obj',
        )
        read_only_fields = ('created_at', 'updated_at', 'sample_group_obj', 'pipeline_module_obj')


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


def _presign_ar_field_stored_data_if_appropriate(ret, org):
    if ret['stored_data'].get('__type__', '').lower() != 's3':
        return ret
    bucket_name = ret['stored_data']['uri'].split('s3://')[1].split('/')[0]
    s3bucket_query = org.s3bucket_set \
        .filter(endpoint_url=ret['stored_data']['endpoint_url']) \
        .filter(Q(name=bucket_name))
    if s3bucket_query.exists():
        s3key = s3bucket_query[0].api_key
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
            instance.analysis_result.sample.organization,
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
            instance.analysis_result.sample_group.organization,
        )


class JobOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobOrder
        fields = ('uuid', 'name', 'status', 'work_order', 'pipeline_module',
                  'analysis_result', 'resources_used', 'resources_needed',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class WorkOrderSerializer(serializers.ModelSerializer):

    job_order_objs = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    progress_summary = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrder
        fields = ('uuid', 'name', 'priority', 'sample',
                  'created_at', 'updated_at',
                  'job_order_objs', 'status', 'progress_summary')
        read_only_fields = ('created_at', 'updated_at')

    def get_status(self, obj):
        return obj.status

    def get_progress_summary(self, obj):
        return obj.progress_summary

    def get_job_order_objs(self, obj):
        return [
            JobOrderSerializer(job_order).data
            for job_order in obj.jobs.all()
        ]

class JobOrderProtoSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobOrderProto
        fields = ('uuid', 'name', 'pipeline_module', 'resources_needed',
                  'work_order_proto', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class WorkOrderProtoSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkOrderProto
        fields = ('uuid', 'name', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


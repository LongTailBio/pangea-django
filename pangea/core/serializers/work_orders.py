
from rest_framework import serializers
from django.db.models import Q
import structlog

from ..models import (
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
    GroupWorkOrder,
    JobOrderProto,
    WorkOrderProto,
    GroupWorkOrderProto,
)

logger = structlog.get_logger(__name__)


class JobOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobOrder
        fields = ('uuid', 'name', 'status', 'work_order', 'pipeline_module',
                  'analysis_result', 'resources_used', 'resources_needed',
                  'created_at', 'updated_at', 'description')
        read_only_fields = ('created_at', 'updated_at')


class WorkOrderSerializer(serializers.ModelSerializer):

    job_order_objs = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    progress_summary = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrder
        fields = ('uuid', 'name', 'priority', 'sample',
                  'created_at', 'updated_at', 'description',
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


class GroupWorkOrderSerializer(serializers.ModelSerializer):

    work_order_links = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    progress_summary = serializers.SerializerMethodField()

    class Meta:
        model = GroupWorkOrder
        fields = ('uuid', 'name', 'priority', 'sample_group',
                  'created_at', 'updated_at', 'description',
                  'work_order_links', 'status', 'progress_summary',
                  'work_orders',)
        read_only_fields = ('created_at', 'updated_at')

    def get_status(self, obj):
        return obj.status

    def get_progress_summary(self, obj):
        return obj.progress_summary

    def get_work_order_links(self, obj):
        return [
            {
                'name': wo.name,
                'uuid': wo.uuid,
                'sample_name': wo.sample.name,
                'sample_uuid': wo.sample.uuid,
                'status': wo.status
            }
            for wo in obj.work_orders.all()
        ]


class JobOrderProtoSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobOrderProto
        fields = ('uuid', 'name', 'pipeline_module', 'resources_needed',
                  'work_order_proto', 'created_at', 'updated_at', 'description')
        read_only_fields = ('created_at', 'updated_at')


class WorkOrderProtoSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkOrderProto
        fields = ('uuid', 'name', 'created_at', 'updated_at', 'description')
        read_only_fields = ('created_at', 'updated_at')


class GroupWorkOrderProtoSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupWorkOrderProto
        fields = ('uuid', 'name', 'created_at', 'updated_at', 'description', 'work_order_protos')
        read_only_fields = ('created_at', 'updated_at')

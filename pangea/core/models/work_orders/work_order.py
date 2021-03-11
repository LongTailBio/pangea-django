
from pangea.core.mixins import AutoCreatedUpdatedMixin
from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import JSONField


class JobOrderStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    ERROR = 'error', _('Error')
    WORKING = 'working', _('Working')
    SUCCESS = 'success', _('Success')


class JobOrder(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)
    status = models.TextField(choices=JobOrderStatus.choices, default=JobOrderStatus.PENDING)
    work_order = models.ForeignKey('WorkOrder', on_delete=models.CASCADE, related_name='jobs')
    prototype = models.ForeignKey('JobOrderProto', on_delete=models.CASCADE)
    pipeline_module = models.ForeignKey(
        'PipelineModule', on_delete=models.SET_NULL, related_name='job_orders', null=True
    )
    analysis_result = models.OneToOneField(
        'SampleAnalysisResult', on_delete=models.SET_NULL, related_name='job_order', null=True
    )
    resources_used = JSONField(blank=True, default=dict)
    resources_needed = JSONField(blank=True, default=dict)

    def user_is_privileged(self, user):
        return self.prototype.user_is_privileged(user)


class WorkOrder(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)
    priority = models.IntegerField(default=100)
    sample = models.ForeignKey('Sample', on_delete=models.CASCADE, related_name='work_orders')
    prototype = models.ForeignKey('WorkOrderProto', on_delete=models.CASCADE)

    def user_is_privileged(self, user):
        return self.prototype.user_is_privileged(user)

    @property
    def status(self):
        statuses = {}
        for job in self.jobs:
            statuses[job.status] = 1 + statuses.get(job.status, 0)
        if statuses.get(JobOrderStatus.ERROR, 0) > 0:
            return JobOrderStatus.ERROR
        if statuses.get(JobOrderStatus.PENDING, 0) == len(self.jobs):
            return JobOrderStatus.PENDING
        if statuses.get(JobOrderStatus.SUCCESS, 0) == len(self.jobs):
            return JobOrderStatus.SUCCESS
        return JobOrderStatus.WORKING

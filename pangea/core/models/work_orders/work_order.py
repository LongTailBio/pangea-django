
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
    pipeline_module = models.ForeignKey(
        'PipelineModule', on_delete=models.CASCADE, related_name='job_orders'
    )
    analysis_result = models.OneToOneField(
        'SampleAnalysisResult', on_delete=models.SET_NULL, related_name='job_order', null=True
    )
    resources_used = JSONField(blank=True, default=dict)
    resources_needed = JSONField(blank=True, default=dict)


class WorkOrder(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)
    priority = models.IntegerField(default=100)
    sample = models.ForeignKey('Sample', on_delete=models.CASCADE, related_name='work_orders')

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

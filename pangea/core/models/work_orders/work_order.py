
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
    description = models.TextField(blank=True, default='')

    def user_is_privileged(self, user):
        return self.prototype.user_is_privileged(user)


class WorkOrder(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)
    priority = models.IntegerField(default=100)
    sample = models.ForeignKey('Sample', on_delete=models.CASCADE, related_name='work_orders')
    prototype = models.ForeignKey('WorkOrderProto', on_delete=models.CASCADE)
    description = models.TextField(blank=True, default='')

    def user_is_privileged(self, user):
        return self.prototype.user_is_privileged(user)

    @property
    def progress_summary(self):
        statuses = {}
        for job in self.jobs.all():
            statuses[job.status] = 1 + statuses.get(job.status, 0)
        statuses['n_jobs'] = self.jobs.count()
        return statuses

    @property
    def status(self):
        statuses = self.progress_summary
        if statuses.get(JobOrderStatus.ERROR, 0) > 0:
            return JobOrderStatus.ERROR
        if statuses.get(JobOrderStatus.PENDING, 0) == self.jobs.count():
            return JobOrderStatus.PENDING
        if statuses.get(JobOrderStatus.SUCCESS, 0) == self.jobs.count():
            return JobOrderStatus.SUCCESS
        return JobOrderStatus.WORKING


class GroupWorkOrder(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)
    priority = models.IntegerField(default=100)
    sample_group = models.ForeignKey('SampleGroup', on_delete=models.CASCADE, related_name='work_orders')
    prototype = models.ForeignKey('GroupWorkOrderProto', on_delete=models.CASCADE)
    description = models.TextField(blank=True, default='')
    work_orders = models.ManyToManyField('WorkOrder', null=True, blank=True)

    def user_is_privileged(self, user):
        return self.prototype.user_is_privileged(user)

    @property
    def progress_summary(self):
        statuses = {}
        for wo in self.work_orders.all():
            for status, count in wo.progress_summary.items():
                statuses[status] = count + statuses.get(status, 0)
        return statuses

    @property
    def status(self):
        statuses = self.progress_summary
        if statuses.get(JobOrderStatus.ERROR, 0) > 0:
            return JobOrderStatus.ERROR
        if statuses.get(JobOrderStatus.PENDING, 0) == statuses['n_jobs']:
            return JobOrderStatus.PENDING
        if statuses.get(JobOrderStatus.SUCCESS, 0) == statuses['n_jobs']:
            return JobOrderStatus.SUCCESS
        return JobOrderStatus.WORKING

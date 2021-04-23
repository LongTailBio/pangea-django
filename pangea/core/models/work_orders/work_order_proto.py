from pangea.core.mixins import AutoCreatedUpdatedMixin
from django.db import models
import uuid
from django.contrib.postgres.fields import JSONField

from .work_order import JobOrder, WorkOrder, GroupWorkOrder


class JobOrderProto(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)
    pipeline_module = models.ForeignKey(
        'PipelineModule', null=True,
        on_delete=models.SET_NULL, related_name='job_order_protos'
    )
    resources_needed = JSONField(blank=True, default=dict)
    work_order_proto = models.ForeignKey(
        'WorkOrderProto', on_delete=models.CASCADE, related_name='job_protos'
    )
    description = models.TextField(blank=True, default='')

    def user_is_privileged(self, user):
        return self.work_order_proto.user_is_privileged(user)

    def job_order(self, work_order):
        """Return a job order created from this prototype."""
        job = JobOrder(
            name=self.name,
            work_order=work_order,
            pipeline_module=self.pipeline_module,
            resources_needed=self.resources_needed,
            prototype=self,
            description=self.description,
        )
        job.save()
        return job


class WorkOrderProto(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)
    description = models.TextField(blank=True, default='')

    def user_is_privileged(self, user):
        return self.privileged_users.filter(user__pk=user.pk).exists()

    def work_order(self, sample):
        """Return a work order from this prototype and sample."""
        work = WorkOrder(
            name=self.name, sample=sample,
            prototype=self, description=self.description
        )
        work.save()
        for job_proto in self.job_protos.all():
            job_proto.job_order(work)
        return work


class GroupWorkOrderProto(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)
    description = models.TextField(blank=True, default='')
    work_order_protos = models.ManyToManyField('WorkOrderProto', null=True, blank=True)

    def user_is_privileged(self, user):
        privileged, empty = True, True
        for wop in self.work_order_protos.all():
            empty = False
            privileged = privileged and wop.user_is_privileged(user)
        if empty:
            return False
        return privileged

    def work_order(self, sample_group):
        """Return a GroupWorkOrder from this prototype and sample group."""
        work = GroupWorkOrder(
            name=self.name, sample_group=sample_group,
            prototype=self, description=self.description,
        )
        for sample in sample_group.sample_set.all():
            for wop in self.work_order_protos.all():
                work.work_orders.add(wop.work_order(sample))
        work.save()
        return work



from pangea.core.mixins import AutoCreatedUpdatedMixin
from django.db import models
import uuid
from django.contrib.postgres.fields import JSONField

from .work_order import JobOrder, WorkOrder


class JobOrderProto(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)
    pipeline_module = models.ForeignKey(
        'PipelineModule', on_delete=models.CASCADE, related_name='job_orders'
    )
    resources_needed = JSONField(blank=True, default=dict)
    work_order_proto = models.ForeignKey(
        'WorkOrderProto', on_delete=models.CASCADE, related_name='job_protos'
    )

    def job_order(self, work_order):
        """Return a job order created from this prototype."""
        job = JobOrder(
            name=self.name,
            work_order=work_order,
            pipeline_module=self.pipeline_module,
            resources_needed=self.resources_needed,
        )
        job.save()
        return job


class WorkOrderProto(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, db_index=True)

    def work_order(self, sample):
        """Return a work order from this prototype and sample."""
        work = WorkOrder(name=self.name, sample=sample)
        work.save()
        for job_proto in self.job_protos:
            job_proto.job_order(work)
        return work

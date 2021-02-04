
from django.contrib.postgres.fields import JSONField
from django.db import models

import uuid
import structlog

from pangea.core.mixins import AutoCreatedUpdatedMixin

logger = structlog.get_logger(__name__)


class PipelineModule(AutoCreatedUpdatedMixin):
    """This class represents a module in a pipeline."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=False)
    version = models.TextField(blank=False, unique=False)
    pipeline = models.ForeignKey('Pipeline', on_delete=models.CASCADE, related_name='modules')
    description = models.TextField(blank=False, default='')
    long_description = models.TextField(blank=True, default='')
    metadata = JSONField(blank=True, default=dict)

    class Meta:
        unique_together = (('pipeline', 'name', 'version'),)

    def __str__(self):
        return f'<PipelineModule name="{self.name}" pipeline="{self.pipeline.name}">'

    def __repr__(self):
        return f'<PipelineModule name="{self.name}" pipeline="{self.pipeline.name}">'

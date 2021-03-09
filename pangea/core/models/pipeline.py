
from django.contrib.postgres.fields import JSONField
from django.db import models

import uuid
import structlog

from pangea.core.mixins import AutoCreatedUpdatedMixin

from .pipeline_module import PipelineModule

logger = structlog.get_logger(__name__)


class Pipeline(AutoCreatedUpdatedMixin):
    """This class represents a pipeline (as a collection of modules)."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    description = models.TextField(blank=True, default='')
    long_description = models.TextField(blank=True, default='')

    def create_module(self, **kwargs):
        pm = PipelineModule.objects.create(pipeline=self, **kwargs)
        return pm

    def __str__(self):
        return f'<Pipeline uuid="{self.uuid}" name="{self.name}">'

    def __repr__(self):
        return f'<Pipeline uuid="{self.uuid}" name="{self.name}">'

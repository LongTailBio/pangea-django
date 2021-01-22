from pangea.core.mixins import AutoCreatedUpdatedMixin
from django.contrib.postgres.fields import JSONField
import structlog
from django.db import models

logger = structlog.get_logger(__name__)


class VersionedMetadata(AutoCreatedUpdatedMixin):
    """This class represents the sample model."""
    metadata = JSONField(blank=True, default=dict)
    sample = models.ForeignKey(
        'Sample', on_delete=models.CASCADE, related_name='versioned_metadata', null=True
    )

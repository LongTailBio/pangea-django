from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

import uuid
import boto3
from botocore.exceptions import ClientError
import structlog

from pangea.core.exceptions import SampleOwnerError
from pangea.core.managers import PangeaUserManager
from pangea.core.mixins import AutoCreatedUpdatedMixin
from pangea.core.utils import random_replicate_name
from pangea.core.encrypted_fields import EncryptedTextField

from .analysis_result import SampleAnalysisResult

logger = structlog.get_logger(__name__)


class Sample(AutoCreatedUpdatedMixin):
    """This class represents the sample model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=False)
    library = models.ForeignKey(
        'SampleLibrary', on_delete=models.CASCADE, related_name='owned_samples'
    )
    sample_groups = models.ManyToManyField('SampleGroup')
    metadata = JSONField(default=dict)
    description = models.TextField(blank=False, default='')

    class Meta:
        unique_together = (('name', 'library'),)

    @property
    def organization(self):
        return self.library.group.organization

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f'<Sample name="{self.name}" library="{self.library.group.name}">'

    def create_analysis_result(self, *args, **kwargs):
        ar = SampleAnalysisResult.objects.create(sample=self, *args, **kwargs)
        return ar

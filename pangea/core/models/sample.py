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
from .versioned_metadata import VersionedMetadata

logger = structlog.get_logger(__name__)


class Sample(AutoCreatedUpdatedMixin):
    """This class represents the sample model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=False)
    library = models.ForeignKey(
        'SampleLibrary', on_delete=models.CASCADE, related_name='owned_samples'
    )
    sample_groups = models.ManyToManyField('SampleGroup')
    description = models.TextField(blank=True, default='')
    _cached_metadata = None

    class Meta:
        unique_together = (('name', 'library'),)

    def save(self, *args, **kwargs):
        new_meta = kwargs.pop('metadata', self._cached_metadata)
        if new_meta is not None:
            self.save_versioned_metadata(new_meta)
        super(Sample, self).save(*args, **kwargs)

    @property
    def is_public(self):
        return self.library.group.is_public

    @property
    def organization(self):
        return self.library.group.organization

    @property
    def metadata(self):
        try:
            return self.versioned_metadata.order_by('-updated_at')[0].metadata
        except IndexError:
            return {}

    @metadata.setter
    def metadata(self, new_meta):
        self._cached_metadata = new_meta

    def save_versioned_metadata(self, new_meta):
        if new_meta and new_meta == self.metadata:
            # update the timestamp on the versioned metadata but otherwise do nothing
            self.versioned_metadata.order_by('-updated_at')[0].save()
            return
        vmeta = VersionedMetadata.objects.create(sample=self, metadata=new_meta)
        vmeta.save()

    def save_revert_metadata(self, steps):
        metadata_to_revert_to = self.versioned_metadata.order_by('-updated_at')[steps]
        metadata_to_revert_to.save()  # update the timestamp

    def user_can_view(self, user):
        """Return True iff `user` can perform read-only operations on this sample."""
        return self.library.group.user_can_view(user)

    def user_can_access(self, user):
        """Return True iff `user` can perform any operation on this sample."""
        return self.library.group.user_can_access(user)

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f'<Sample name="{self.name}" library="{self.library.group.name}">'

    def create_analysis_result(self, *args, **kwargs):
        ar = SampleAnalysisResult.objects.create(sample=self, *args, **kwargs)
        return ar

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
from pangea.core.models import (
    Sample,
    SampleGroup,
)

logger = structlog.get_logger(__name__)


class Tag(AutoCreatedUpdatedMixin):
    """This class represents the sample model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    payload = models.TextField(blank=True, unique=False)

    def add_related_tag(self, tag, payload=''):
        relate = TagTagRelationship(tag=self, other_tag=tag, payload=payload)
        relate.save()
        return self

    def tag_sample_group(self, sample_group, payload=''):
        relate = SampleGroupTagRelationship(tag=self, sample_group=sample_group, payload=payload)
        relate.save()
        return self

    def tag_sample(self, sample, payload=''):
        relate = SampleTagRelationship(tag=self, sample=sample, payload=payload)
        relate.save()
        return self

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f'<Tag name="{self.name}" payload="{self.payload}">'


class GenericTagRelationship(AutoCreatedUpdatedMixin):
    payload = models.TextField(blank=True, unique=False)

    class Meta:
        abstract = True


class TagTagRelationship(GenericTagRelationship):
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE, related_name='related_tags')
    other_tag = models.ForeignKey('Tag', on_delete=models.CASCADE, related_name='back_related_tags')


class SampleGroupTagRelationship(GenericTagRelationship):
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE, related_name='tagged_sample_groups')
    sample_group = models.ForeignKey(SampleGroup, on_delete=models.CASCADE, related_name='tags')


class SampleTagRelationship(GenericTagRelationship):
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE, related_name='tagged_samples')
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='tags')

    def __str__(self):
        return f'<SampleTagRelationShip tag="{self.tag}" sample="{self.sample}" payload="{self.payload}">'

    def __repr__(self):
        return f'<SampleTagRelationShip tag="{self.tag}" sample="{self.sample}" payload="{self.payload}">'


from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError

import uuid
import pandas as pd
import boto3
from botocore.exceptions import ClientError
import structlog

from pangea.core.exceptions import SampleOwnerError
from pangea.core.managers import PangeaUserManager
from pangea.core.mixins import AutoCreatedUpdatedMixin
from pangea.core.utils import random_replicate_name
from pangea.core.encrypted_fields import EncryptedTextField

from .sample import Sample
from .analysis_result import SampleGroupAnalysisResult

logger = structlog.get_logger(__name__)


class SampleGroup(AutoCreatedUpdatedMixin):
    """This class represents the sample group model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    description = models.TextField(blank=False, default='')
    long_description = models.TextField(blank=True, default='')
    metadata = JSONField(blank=True, default=dict)
    sample_metadata_schema = JSONField(blank=False, default=dict)

    is_public = models.BooleanField(blank=False, default=True)
    is_library = models.BooleanField(blank=False, default=False)
    theme = models.TextField(blank=True)
    bucket = models.ForeignKey('S3Bucket', on_delete=models.SET_NULL, null=True)
    storage_provider_name = models.TextField(blank=False, default='custom')
    guest_users = models.ManyToManyField(settings.AUTH_USER_MODEL)

    def save(self, *args, **kwargs):
        out = super(SampleGroup, self).save(*args, **kwargs)
        if self.is_library:  # New SampleGroup
            lib, created = SampleLibrary.objects.get_or_create(group=self)
            if created:
                lib.save()
                logger.info(
                    'created_library',
                    group_uuid=lib.group.uuid,
                )
        logger.info(
            'saved_sample_group',
            obj_uuid=self.uuid,
            saved_uuid=out.uuid,
            name=self.name,
            is_library=self.is_library,
        )
        return out

    def user_can_access(self, user):
        """Return True iff `user` can perform any operation on this group."""
        if not user.is_authenticated:
            return False
        user_is_in_org = user.organization_set.filter(pk=self.organization.pk).exists()
        user_is_guest = user in self.guest_users.all()
        return user_is_in_org or user_is_guest

    def create_sample(self, *args, **kwargs):
        if not self.is_library:
            raise SampleOwnerError('Only libraries can create samples')
        sample = self.library.create_sample(*args, **kwargs)
        return sample

    def add_sample(self, sample):
        sample.sample_groups.add(self)
        self.save()
        sample.save()
        return self

    def add_s3_bucket(self, bucket):
        self.bucket = bucket
        self.save()
        return self

    def create_analysis_result(self, *args, **kwargs):
        ar = SampleGroupAnalysisResult.objects.create(sample_group=self, *args, **kwargs)
        return ar

    def sample_metadata(self):
        """Return a dict of sample metadata."""
        metadata = {}
        for sample in self.sample_set.all():
            metadata[sample.name] = sample.metadata
        return metadata

    def generate_sample_metadata_schema(self, overwrite=False):
        """Generate a Table Schema based on existing metadata."""
        if self.sample_metadata_schema and not overwrite:
            logger.warn(
                'no_overwrite_existing_sample_metadata_schema',
                group_uuid=self.uuid,
                schema=self.sample_metadata_schema,
            )
            raise ValidationError('no_overwrite_existing_sample_metadata_schema')
        logger.info(
            'generating_sample_metadata_schema',
            group_uuid=self.uuid,
        )
        metadata = self.sample_metadata()
        tbl = pd.DataFrame.from_dict(metadata, orient='index')
        schema = pd.io.json.build_table_schema(tbl, version=False, index=False, primary_key=None)
        self.sample_metadata_schema = schema
        self.save()


    @classmethod
    def factory(cls, *args, **kwargs):
        grp = cls.objects.create(*args, **kwargs)
        if grp.is_library:
            SampleLibrary.objects.get_or_create(group=grp)
        return grp

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return f'<SampleGroup name="{self.name}" organization="{self.organization.name}">'


class SampleLibrary(AutoCreatedUpdatedMixin):
    group = models.OneToOneField(
        SampleGroup,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='library'
    )

    def create_sample(self, *args, **kwargs):
        sample = Sample.objects.create(library=self, *args, **kwargs)
        self.group.add_sample(sample)
        return sample

    def __str__(self):
        return f'{self.group.name} (library)'

    def __repr__(self):
        return f'<SampleLibrary name="{self.group.name}">'

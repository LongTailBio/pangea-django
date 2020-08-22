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

from .sample_group import SampleGroup
from .s3 import S3Bucket

logger = structlog.get_logger(__name__)


class PangeaUser(AbstractUser):
    """Custom Pangea user type."""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    personal_org_uuid = models.UUIDField(blank=True, null=True)
    saved_sample_groups = models.ManyToManyField('SampleGroup')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = PangeaUserManager()

    def __str__(self):
        return self.email

    @property
    def _personal_org_name(self):
        return f'Personal Organization for User {self.email}'

    @property
    def personal_org(self):
        try:
            return Organization.objects.get(pk=self.personal_org_uuid)
        except ObjectDoesNotExist:
            org = Organization.objects.create(name=self._personal_org_name)
            org.users.add(self)
            org.save()
            self.personal_org_uuid = org.uuid
            self.save()
            return org


class Organization(AutoCreatedUpdatedMixin):
    """This class represents the organization model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    users = models.ManyToManyField(get_user_model())
    core_sample_group_uuid = models.UUIDField(blank=True, null=True)

    def save(self, *args, **kwargs):
        out = super(Organization, self).save(*args, **kwargs)
        logger.info(
            'saved_organization',
            obj_uuid=self.uuid,
            saved_uuid=out.uuid,
            name=self.name,
        )
        return out

    def create_sample_group(self, *args, **kwargs):
        sample_group = SampleGroup.factory(organization=self, *args, **kwargs)
        return sample_group

    def create_s3bucket(self, *args, **kwargs):
        s3bucket = S3Bucket(organization=self, *args, **kwargs)
        s3bucket.save()
        return s3bucket

    @property
    def _core_sample_group_name(self):
        return f'Default Sample Group for Organization {self.name}'

    @property
    def core_sample_group(self):
        try:
            return SampleGroup.objects.get(pk=self.core_sample_group_uuid)
        except ObjectDoesNotExist:
            grp = SampleGroup.factory(
                name=self._core_sample_group_name,
                organization=self,
                is_public=False,
                is_library=True,
            )
            self.core_sample_group_uuid = grp.uuid
            self.save()
            return grp

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return f'<Organization name="{self.name}">'

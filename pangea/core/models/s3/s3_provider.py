from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response

import uuid
import boto3
from botocore.exceptions import ClientError
import structlog

from pangea.core.exceptions import SampleOwnerError
from pangea.core.managers import PangeaUserManager
from pangea.core.mixins import AutoCreatedUpdatedMixin
from pangea.core.utils import random_replicate_name
from pangea.core.encrypted_fields import EncryptedTextField
from pangea.core.custom_fields import AtMostOneBooleanField

from .s3_bucket import S3Bucket
from .s3_api_key import S3ApiKey
from .s3_management import create_usable_bucket_on_s3

logger = structlog.get_logger(__name__)


class S3Provider(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    s3_endpoint_url = models.TextField(blank=False)
    iam_endpoint_url = models.TextField(blank=False)
    public_key = models.TextField(blank=False, default=None)
    private_key = EncryptedTextField(blank=False, default=None)
    default_provider = AtMostOneBooleanField(default=False)

    def __str__(self):
        return f'<S3Provider name="{self.name}" uuid="{self.uuid}">'

    def __repr__(self):
        return f'<S3Provider name="{self.name}" uuid="{self.uuid}">'

    @property
    def s3(self):
        return boto3.client(
            's3',
            endpoint_url=self.s3_endpoint_url,
            region_name='us-east-1',
            aws_access_key_id=self.public_key,
            aws_secret_access_key=self.private_key.decrypt(),
        )

    @property
    def iam(self):
        return boto3.client(
            'iam',
            endpoint_url=self.iam_endpoint_url,
            region_name='us-east-1',
            aws_access_key_id=self.public_key,
            aws_secret_access_key=self.private_key.decrypt(),
        )

    def create_bucket(self, sample_group):
        bucket_name = f'pangea.v1.{sample_group.uuid}'
        user_info = create_usable_bucket_on_s3(bucket_name, self.s3, self.iam)
        bucket = S3Bucket(
            name=bucket_name,
            endpoint_url=self.s3_endpoint_url,
            organization=sample_group.organization,
            storage_provider=self,
        )
        bucket.save()
        api_key = S3ApiKey(
            description='read write',
            public_key=user_info['public_key'],
            private_key=user_info['private_key'],
            bucket=bucket,
        )
        api_key.save()
        sample_group.add_s3_bucket(bucket)
        return bucket, api_key

    @classmethod
    def get_provider_by_name(cls, name):
        name = name.lower()
        if name == 'custom':
            return None
        elif name == 'default':
            default_provider = cls.objects.filter(default_provider=True)
            if default_provider.exists():
                return default_provider.get()
            else:
                return None
        provider = cls.objects.filter(name=name)
        if provider.exists():
            return provider
        return None

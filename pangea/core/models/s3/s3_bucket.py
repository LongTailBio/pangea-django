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

from .s3_api_key import S3ApiKey

logger = structlog.get_logger(__name__)


class S3Bucket(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=False)
    endpoint_url = models.TextField(blank=False)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=False)
    storage_provider = models.ForeignKey(
        'S3Provider', on_delete=models.SET_NULL, null=True, blank=True, related_name='buckets'
    )

    def create_s3apikey(self, *args, **kwargs):
        s3apikey = S3ApiKey(bucket=self, *args, **kwargs)
        s3apikey.save()
        return s3apikey

    def presign_url(self, s3_url, **kwargs):
        return self.api_key.presign_url(self.endpoint_url, s3_url, **kwargs)

    def presign_completion_url(self, s3_url, upload_id, parts, **kwargs):
        return self.api_key.presign_completion_url(
            self.endpoint_url, s3_url, upload_id, parts, **kwargs
        )

    def __str__(self):
        return f'<S3Bucket name="{self.name}" uuid="{self.uuid}">'

    def __repr__(self):
        return f'<S3Bucket name="{self.name}" uuid="{self.uuid}">'

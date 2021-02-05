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

logger = structlog.get_logger(__name__)


class S3MultipartUploadUtil:
    """AWS S3 Multipart Upload Util"""

    def __init__(self, api_key, s3_file_key):
        self.api_key = api_key
        self.s3 = self.api_key.s3
        self.s3_file_key = s3_file_key
        res = self.s3.create_multipart_upload(
            Bucket=self.api_key.bucket.name,
            Key=self.s3_file_key
        )
        self.upload_id = res['UploadId']
        self.part_no = 1

    def create_presigned_url(self, part_no=None, timeout_hours=24):
        part_no = self.part_no if part_no is None else part_no
        signed_url = self.s3.generate_presigned_url(
            ClientMethod='upload_part',
            Params={
                'Bucket': self.api_key.bucket.name,
                'Key': self.s3_file_key,
                'UploadId': self.upload_id,
                'PartNumber': part_no
            },
            ExpiresIn=(timeout_hours * 60 * 60)
        )
        self.part_no += 1
        return signed_url

    def create_complete_url(self, upload_id, parts, timeout_hours=24):
        res = self.s3.complete_multipart_upload(
            Bucket=self.api_key.bucket.name,
            Key=self.s3_file_key,
            MultipartUpload={'Parts': parts},
            UploadId=upload_id
        )
        return {'status': 'success', 'upload_id': upload_id}

class S3ApiKey(AutoCreatedUpdatedMixin):
    """Represent an S3 API Key.

    At present S3 API keys will be used by an organization to generate
    short lived presigned URLs to download objects from S3. They will
    not be used to upload data at this point.

    Each API key must be assigned to a particular endpoint url.
    Each API key can be assigned to a particular bucket or '*'
    for all buckets.

    S3ApiKey.private_key should never need to be sent to the client.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(blank=False, default='')
    public_key = models.TextField(blank=False, default=None)
    private_key = EncryptedTextField(blank=False, default=None)
    bucket = models.OneToOneField(
        'S3Bucket', on_delete=models.CASCADE, related_name='api_key'
    )

    def save(self, *args, **kwargs):
        out = super(S3ApiKey, self).save(*args, **kwargs)
        logger.info(
            'saved_s3apikey',
            obj_uuid=self.uuid,
            public_key=self.public_key,
        )
        return out

    def __str__(self):
        return f'<S3ApiKey uuid="{self.uuid}" public_key="{self.public_key}">'

    def __repr__(self):
        return f'<S3ApiKey uuid="{self.uuid}" public_key="{self.public_key}">'

    @property
    def s3(self):
        return boto3.client(
            's3',
            endpoint_url=self.bucket.endpoint_url,
            aws_access_key_id=self.public_key,
            aws_secret_access_key=self.private_key.decrypt(),
        )

    def _prep_presign(self, endpoint_url, s3_url):
        if endpoint_url != self.bucket.endpoint_url:
            msg = f'Endpoint URL {endpoint_url} does not match that specified for key {self}'
            raise ValueError(msg)
        bucket_name = s3_url.split('s3://')[1].split('/')[0]
        if self.bucket.name != bucket_name:
            msg = f'URI "{s3_url}" {bucket_name} does not match bucket "{self.bucket.name}"'
            raise ValueError(msg)
        object_name = s3_url.split(f's3://{bucket_name}/')[1]
        return bucket_name, object_name

    def presign_url(self, endpoint_url, s3_url, timeout_hours=24, stance='download', n_parts=1):
        """Return a presigned version of the url."""
        bucket_name, object_name = self._prep_presign(endpoint_url, s3_url)
        try:
            if stance == 'download':
                response = self.s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': object_name},
                    ExpiresIn=(timeout_hours * 60 * 60)
                )
                return response  # The response contains the presigned URL
            elif stance == 'upload':
                response = self.s3.generate_presigned_post(
                    bucket_name,
                    object_name,
                    ExpiresIn=(timeout_hours * 60 * 60)
                )
                return response
            elif stance == 'upload-multipart':
                s3util = S3MultipartUploadUtil(self, object_name)
                urls = [
                    s3util.create_presigned_url(timeout_hours=timeout_hours)
                    for _ in range(n_parts)
                ]
                return {
                    'urls': urls,
                    'upload_id': s3util.upload_id,
                }
            else:
                assert False, f'Stance "{stance}" is invlaid. Must be one of: "upload", "download", "upload-multipart'
        except ClientError:
            logger.exception(
                'create_presigned_url_exception',
                s3_url=s3_url,
                endpoint_url=endpoint_url,
                bucket=bucket_name,
                timeout_hours=timeout_hours,
            )
            return None

    def presign_completion_url(self, endpoint_url, s3_url, upload_id,parts, timeout_hours=24):
        """Return a presigned version of the url."""
        bucket_name, object_name = self._prep_presign(endpoint_url, s3_url)
        try:
            s3util = S3MultipartUploadUtil(self, object_name)
            return s3util.create_complete_url(upload_id,parts, timeout_hours=timeout_hours)
        except ClientError:
            logger.exception(
                'create_presigned_url_exception',
                s3_url=s3_url,
                endpoint_url=endpoint_url,
                bucket=bucket_name,
                timeout_hours=timeout_hours,
            )
            return None


class S3Bucket(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=False)
    endpoint_url = models.TextField(blank=False)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=False)

    def create_s3apikey(self, *args, **kwargs):
        s3apikey = S3ApiKey(bucket=self, *args, **kwargs)
        s3apikey.save()
        return s3apikey

    def presign_url(self, s3_url, **kwargs):
        return self.api_key.presign_url(self.endpoint_url, s3_url, **kwargs)

    def presign_completion_url(self, s3_url, upload_id, parts, **kwargs):
        return self.api_key.presign_completion_url(self.endpoint_url, s3_url, upload_id, parts, **kwargs)

    def __str__(self):
        return f'<S3Bucket name="{self.name}" uuid="{self.uuid}">'

    def __repr__(self):
        return f'<S3Bucket name="{self.name}" uuid="{self.uuid}">'

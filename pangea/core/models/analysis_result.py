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
from .exceptions import AnalysisResultFieldError

logger = structlog.get_logger(__name__)


class AnalysisResult(AutoCreatedUpdatedMixin):
    """Represent a single field of a single result in the database.

    Example:
        KrakenUniq produces a table of read-classifications and a report.
        These are stored separately as two separate AnalysisResults.
        Both ARs have the same `module_name` (e.g. KrakenUniq)
        Both ARs have the same owner (e.g. sample-123)
        Both ARs have different a `field_name` (e.g. report or read_class).
    `owner_uuid` should reference a group or sample. Whether it is a group
    or sample is determined by `owned_by_group`. This is only enforced in
    code. The reverse (sample->AR or group->AR) is enforced in SQL.
    AR Fields carry a status marker. In principle all fields of an ARs always
    have the same status.
    """

    class AnalysisResultStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ERROR = 'error', _('Error')
        WORKING = 'working', _('Working')
        SUCCESS = 'success', _('Success')

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module_name = models.TextField(blank=False, db_index=True)
    # TODO: document `replicate` field in DocString
    replicate = models.TextField(blank=False, db_index=False, default=random_replicate_name)
    status = models.TextField(
        choices=AnalysisResultStatus.choices,
        default=AnalysisResultStatus.PENDING,
    )
    metadata = JSONField(blank=True, default=dict)
    description = models.TextField(blank=True, default='')

    # If true treat this AR as if it was private regardless of its parent's status
    is_private = models.BooleanField(blank=False, default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        return super(AnalysisResult, self).save(*args, **kwargs)


class SampleAnalysisResult(AnalysisResult):
    """Class representing a single field of a sample analysis result."""
    sample = models.ForeignKey(
        'Sample', on_delete=models.CASCADE, related_name='analysis_result_set'
    )

    class Meta:
        unique_together = (('module_name', 'replicate', 'sample'),)

    def save(self, *args, **kwargs):
        out = super(SampleAnalysisResult, self).save(*args, **kwargs)
        logger.info(
            'saved_sample_analysis_result',
            obj_uuid=self.uuid,
            saved_uuid=out.uuid,
            module_name=self.module_name,
            sample={'uuid': self.sample.uuid, 'name': self.sample.name},
            status=self.status,
        )
        return out

    def create_field(self, *args, **kwargs):
        field = SampleAnalysisResultField.objects.create(analysis_result=self, *args, **kwargs)
        return field

    def user_can_access(self, user):
        """Return True iff `user` can perform any operation on this ar."""
        return self.sample.user_can_access(user)

    def __str__(self):
        return f"{self.sample.name} ({self.module_name})"

    def __repr__(self):
        return f'<SampleAnalysisResult uuid="{self.uuid}" module_name="{self.module_name}">'


class SampleGroupAnalysisResult(AnalysisResult):
    """Class representing a single field of a sample group analysis result."""
    sample_group = models.ForeignKey(
        'SampleGroup', on_delete=models.CASCADE, related_name='analysis_result_set'
    )

    class Meta:
        unique_together = (('module_name', 'replicate', 'sample_group'),)

    def save(self, *args, **kwargs):
        out = super(SampleGroupAnalysisResult, self).save(*args, **kwargs)
        logger.info(
            'saved_sample_group_analysis_result',
            obj_uuid=self.uuid,
            saved_uuid=out.uuid,
            module_name=self.module_name,
            sample_group={'uuid': self.sample_group.uuid, 'name': self.sample_group.name},
            status=self.status,
        )
        return out

    def create_field(self, *args, **kwargs):
        field = SampleGroupAnalysisResultField.objects.create(analysis_result=self, *args, **kwargs)
        return field

    def user_can_access(self, user):
        """Return True iff `user` can perform any operation on this ar."""
        return self.sample_group.user_can_access(user)

    def __str__(self):
        return f"{self.sample_group.name} ({self.module_name})"

    def __repr__(self):
        return f'<SampleGroupAnalysisResult uuid="{self.uuid}" module_name="{self.module_name}">'


class AnalysisResultField(AutoCreatedUpdatedMixin):
    """Class representing a single field of a single result in the database."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False)
    stored_data = JSONField(blank=False)

    class Meta:
        abstract = True
        unique_together = (('analysis_result', 'name'),)

    def save(self, *args, **kwargs):
        return super(AnalysisResultField, self).save(*args, **kwargs)

    @property
    def field_type(self):
        if not self.stored_data:
            return 'empty'
        return self.stored_data.get('__type__', 'blob')

    def as_s3_link(self, filename, overwrite_ok=False):
        """Set the stored data of this result-field to contain info for a file stored on S3.

        Return this AR-field for convenience
        """
        if self.stored_data and not overwrite_ok:
            raise AnalysisResultFieldError('Creating S3 result would overwrite existing data')
        self.stored_data = {
            '__type__': 's3',
            'uri': self._as_s3_link(filename),
            'endpoint_url': self.bucket.endpoint_url,
        }
        self.save()
        return self

    def get_presigned_upload_url(self, **kwargs):
        """Return a presigned URL for file upload for this result."""
        if self.stored_data.get('__type__', None) != 's3':
            raise AnalysisResultFieldError(f'AnalysisResultField {self} is not an S3 link')
        self.stored_data['upload_confirmed'] = False
        return self.bucket.presign_url(self.stored_data['uri'], **kwargs)

    def get_presigned_completion_url(self, upload_id, parts, **kwargs):
        """Return a presigned URL for file upload for this result."""
        if self.stored_data.get('__type__', None) != 's3':
            raise AnalysisResultFieldError(f'AnalysisResultField {self} is not an S3 link')
        return self.bucket.presign_completion_url(self.stored_data['uri'], upload_id, parts, **kwargs)


class SampleAnalysisResultField(AnalysisResultField):
    """Class representing an analysis result field for a sample."""
    analysis_result = models.ForeignKey(
        SampleAnalysisResult, on_delete=models.CASCADE, related_name='fields'
    )

    def save(self, *args, **kwargs):
        out = super(SampleAnalysisResultField, self).save(*args, **kwargs)
        logger.info(
            'saved_sample_analysis_result_field',
            obj_uuid=self.uuid,
            saved_uuid=out.uuid,
            field_name=self.name,
            sample_analysis_result={
                'uuid': self.analysis_result.uuid,
                'module_name': self.analysis_result.module_name
            }
        )
        return out

    @property
    def bucket(self):
        return self.analysis_result.sample.library.group.bucket

    def user_can_access(self, user):
        """Return True iff `user` can perform any operation on this ar field."""
        return self.analysis_result.user_can_access(user)

    def _as_s3_link(self, filename):
        lib_name = self.analysis_result.sample.library.group.name
        sample_name = self.analysis_result.sample.name
        uri = f's3://{self.bucket.name}/pangea/v1/{lib_name}/samples/{sample_name}/{filename}'
        return uri

    def __str__(self):
        return f"{self.analysis_result.sample.name} ({self.analysis_result.module_name}: {self.name})"

    def __repr__(self):
        return f'<SampleAnalysisResultField uuid="{self.uuid}" name="{self.name}">'


class SampleGroupAnalysisResultField(AnalysisResultField):
    """Class representing an analysis result field for a sample group."""
    analysis_result = models.ForeignKey(
        SampleGroupAnalysisResult, on_delete=models.CASCADE, related_name='fields'
    )

    @property
    def bucket(self):
        return self.analysis_result.sample_group.bucket

    def save(self, *args, **kwargs):
        out = super(SampleGroupAnalysisResultField, self).save(*args, **kwargs)
        logger.info(
            'saved_sample_group_analysis_result',
            obj_uuid=self.uuid,
            saved_uuid=out.uuid,
            field_name=self.name,
            sample_group_analysis_result={
                'uuid': self.analysis_result.uuid,
                'module_name': self.analysis_result.module_name
            }
        )
        return out

    def _as_s3_link(self, filename):
        """Set the stored data of this result-field to contain info for a file stored on S3.

        Return this AR-field for convenience
        """
        grp_name = self.analysis_result.sample_group.name
        uri = f's3://{self.bucket.name}/pangea/v1/{grp_name}/results/{filename}'
        return uri

    def user_can_access(self, user):
        """Return True iff `user` can perform any operation on this ar field."""
        return self.analysis_result.user_can_access(user)

    def __str__(self):
        return f"{self.analysis_result.sample_group.name} ({self.analysis_result.module_name}: {self.name})"

    def __repr__(self):
        return f'<SampleGroupAnalysisResultField uuid="{self.uuid}" name="{self.name}">'

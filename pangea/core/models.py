from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

import uuid
import boto3
import structlog

from .exceptions import SampleOwnerError
from .managers import PangeaUserManager
from .mixins import AutoCreatedUpdatedMixin
from .utils import random_replicate_name
# from .encrypted_fields import EncryptedTextField

logger = structlog.get_logger(__name__)


class PangeaUser(AbstractUser):
    """Custom Pangea user type."""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    personal_org_uuid = models.UUIDField(blank=True, null=True)

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

    def create_s3apikey(self, *args, **kwargs):
        s3apikey = S3ApiKey(organization=self, *args, **kwargs)
        s3apikey.save()
        return s3apikey

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
    endpoint_url = models.TextField(blank=False)
    bucket = models.TextField(blank=False, default='*')
    public_key = models.TextField(blank=False, default=None)
    private_key = models.TextField(blank=False, default=None)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='s3_api_keys'
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
        return f'{self.public_key}'

    def __repr__(self):
        return f'<S3ApiKey public_key="{self.public_key}">'

    @property
    def s3(self):
        return boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.public_key,
            aws_secret_access_key=self.private_key,
        )

    def presign_url(self, endpoint_url, s3_url, timeout=24):
        """Return a presigned read-only version of the url."""
        assert endpoint_url == self.endpoint_url
        bucket_name = s3_url.split('s3://')[1].split('/')[0]
        assert self.bucket_name in ['*', bucket_name]
        try:
            response = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_name},
                ExpiresIn=(timeout * 60 * 60)
            )
            return response  # The response contains the presigned URL
        except ClientError as e:
            logger.exception(
                'create_presigned_url_exception',
                s3_url=s3_url,
                endpoint_url=endpoint_url,
                bucket=bucket,
                expiration=expiration,
            )
            return None


class SampleGroup(AutoCreatedUpdatedMixin):
    """This class represents the sample group model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    description = models.TextField(blank=False, default='')
    is_public = models.BooleanField(blank=False, default=True)
    is_library = models.BooleanField(blank=False, default=False)
    theme = models.TextField(blank=True)

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

    def create_analysis_result(self, *args, **kwargs):
        ar = SampleGroupAnalysisResult.objects.create(sample_group=self, *args, **kwargs)
        return ar

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


class Sample(AutoCreatedUpdatedMixin):
    """This class represents the sample model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=False)
    library = models.ForeignKey(
        SampleLibrary, on_delete=models.CASCADE, related_name='owned_samples'
    )
    sample_groups = models.ManyToManyField(SampleGroup)
    metadata = JSONField(default=dict)

    class Meta:
        unique_together = (('name', 'library'),)

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f'<Sample name="{self.name}" library="{self.library.group.name}">'

    def create_analysis_result(self, *args, **kwargs):
        ar = SampleAnalysisResult.objects.create(sample=self, *args, **kwargs)
        return ar


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

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        return super(AnalysisResult, self).save(*args, **kwargs)


class SampleAnalysisResult(AnalysisResult):
    """Class representing a single field of a sample analysis result."""
    sample = models.ForeignKey(
        Sample, on_delete=models.CASCADE, related_name='analysis_result_set'
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

    def __str__(self):
        return f"{self.sample.name} ({self.module_name})"

    def __repr__(self):
        return f'<SampleAnalysisResult uuid="{self.uuid}" module_name="{self.module_name}">'


class SampleGroupAnalysisResult(AnalysisResult):
    """Class representing a single field of a sample group analysis result."""
    sample_group = models.ForeignKey(
        SampleGroup, on_delete=models.CASCADE, related_name='analysis_result_set'
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

    def __str__(self):
        return f"{self.analysis_result.sample.name} ({self.analysis_result.module_name}: {self.name})"

    def __repr__(self):
        return f'<SampleAnalysisResultField uuid="{self.uuid}" name="{self.name}">'


class SampleGroupAnalysisResultField(AnalysisResultField):
    """Class representing an analysis result field for a sample group."""
    analysis_result = models.ForeignKey(
        SampleGroupAnalysisResult, on_delete=models.CASCADE, related_name='fields'
    )

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

    def __str__(self):
        return f"{self.analysis_result.sample_group.name} ({self.analysis_result.module_name}: {self.name})"

    def __repr__(self):
        return f'<SampleGroupAnalysisResultField uuid="{self.uuid}" name="{self.name}">'

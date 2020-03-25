from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

import uuid
import random
import structlog

from .exceptions import SampleOwnerError
from .managers import PangeaUserManager
from .mixins import AutoCreatedUpdatedMixin

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
        return f'Personal Organization for User {self.username}'

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


class SampleGroup(AutoCreatedUpdatedMixin):
    """This class represents the sample group model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    description = models.TextField(blank=False, default='')
    is_public = models.BooleanField(blank=False, default=True)
    theme = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        out = super(SampleGroup, self).save(*args, **kwargs)
        logger.info(
            'saved_sample_group',
            obj_uuid=self.uuid,
            saved_uuid=out.uuid,
            name=self.name,
        )
        return out

    @property
    def is_library(self):
        return hasattr(self, 'library')

    def create_sample(self, *args, **kwargs):
        if not self.is_library:
            raise SampleOwnerError('Only libraries can create samples')
        sample = self.library.create_sample(*args, **kwargs)
        return sample

    def add_sample(self, sample):
        sample.sample_groups.add(self)
        sample.save()
        return self

    def create_analysis_result(self, *args, **kwargs):
        ar = SampleGroupAnalysisResult.objects.create(sample_group=self, *args, **kwargs)
        return ar

    @classmethod
    def factory(cls, *args, **kwargs):
        is_library = kwargs.pop('is_library', False)
        grp = cls.objects.create(*args, **kwargs)
        if is_library:
            SampleLibrary.objects.create(group=grp)
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


def random_replicate_name(len=12):
    """Return a random alphanumeric string of length `len`."""
    out = random.choices('abcdefghijklmnopqrtuvwxyzABCDEFGHIJKLMNOPQRTUVWXYZ0123456789', k=len)
    return ''.join(out)


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

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
import random

from .exceptions import SampleOwnerError
from .managers import PangeaUserManager
from .mixins import AutoCreatedUpdatedMixin


class PangeaUser(AbstractUser):
    """Custom Pangea user type."""
    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = PangeaUserManager()

    def __str__(self):
        return self.email


class Organization(AutoCreatedUpdatedMixin):
    """This class represents the organization model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    users = models.ManyToManyField(get_user_model())

    def save(self, *args, **kwargs):
        return super(Organization, self).save(*args, **kwargs)

    def create_sample_group(self, *args, **kwargs):
        sample_group = SampleGroup.factory(organization=self, *args, **kwargs)
        return sample_group

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
        return super(SampleGroup, self).save(*args, **kwargs)

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
        return super(SampleAnalysisResult, self).save(*args, **kwargs)

    def create_field(self, *args, **kwargs):
        field = SampleAnalysisResultField.objects.create(analysis_result=self, *args, **kwargs)
        return field


class SampleGroupAnalysisResult(AnalysisResult):
    """Class representing a single field of a sample group analysis result."""
    sample_group = models.ForeignKey(
        SampleGroup, on_delete=models.CASCADE, related_name='analysis_result_set'
    )

    class Meta:
        unique_together = (('module_name', 'replicate', 'sample_group'),)

    def save(self, *args, **kwargs):
        return super(SampleGroupAnalysisResult, self).save(*args, **kwargs)

    def create_field(self, *args, **kwargs):
        field = SampleGroupAnalysisResultField.objects.create(analysis_result=self, *args, **kwargs)
        return field


class AnalysisResultField(AutoCreatedUpdatedMixin):
    """Class representing a single field of a single result in the database."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    stored_data = JSONField(blank=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        return super(AnalysisResultField, self).save(*args, **kwargs)


class SampleAnalysisResultField(AnalysisResultField):
    """Class representing an analysis result field for a sample."""
    analysis_result = models.ForeignKey(
        SampleAnalysisResult, on_delete=models.CASCADE, related_name='fields'
    )

    def save(self, *args, **kwargs):
        return super(SampleAnalysisResultField, self).save(*args, **kwargs)


class SampleGroupAnalysisResultField(AnalysisResultField):
    """Class representing an analysis result field for a sample group."""
    analysis_result = models.ForeignKey(
        SampleGroupAnalysisResult, on_delete=models.CASCADE, related_name='fields'
    )

    def save(self, *args, **kwargs):
        return super(SampleGroupAnalysisResultField, self).save(*args, **kwargs)

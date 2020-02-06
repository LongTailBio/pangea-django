from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

from .exceptions import SampleOwnerError
from .mixins import AutoCreatedUpdatedMixin


class Organization(AutoCreatedUpdatedMixin):
    """This class represents the organization model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)

    def save(self, *args, **kwargs):
        return super(Organization, self).save(*args, **kwargs)

    def create_sample_group(self, *args, **kwargs):
        sample_group = SampleGroup.object.create(organization=self, *args, **kwargs)
        return sample_group


class SampleGroup(AutoCreatedUpdatedMixin):
    """This class represents the sample group model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    description = models.TextField(blank=False, default='')
    is_library = models.BooleanField(blank=False, default=False)
    is_public = models.BooleanField(blank=False, default=True)
    theme = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        return super(SampleGroup, self).save(*args, **kwargs)

    def create_sample(self, *args, **kwargs):
        if not self.is_library:
            raise SampleOwnerError('Only libraries can create samples')
        sample = Sample.object.create(library=self, *args, **kwargs)
        return sample

    def create_analysis_result(self, *args, **kwargs):
        ar = SampleGroupAnalysisResult.object.create(sample_group=self, *args, **kwargs)
        return ar


class Sample(AutoCreatedUpdatedMixin):
    """This class represents the sample model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    library = models.ForeignKey(SampleGroup, on_delete=models.CASCADE)
    metadata = JSONField()

    class Meta:
        unique_together = (('name', 'library'),)

    def save(self, *args, **kwargs):
        # TODO: ensure that self.library.is_library = True
        return super(Sample, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    def create_analysis_result(self, *args, **kwargs):
        ar = SampleAnalysisResult.object.create(sample=self, *args, **kwargs)
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
    replicate = models.TextField(blank=False, db_index=True)
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
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('module_name', 'replicate', 'sample'),)

    def save(self, *args, **kwargs):
        return super(SampleAnalysisResult, self).save(*args, **kwargs)

    def create_field(self, *args, **kwargs):
        field = SampleAnalysisResultField.object.create(analysis_result=self, *args, **kwargs)
        return field


class SampleGroupAnalysisResult(AnalysisResult):
    """Class representing a single field of a sample group analysis result."""
    sample_group = models.ForeignKey(SampleGroup, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('module_name', 'replicate', 'sample_group'),)

    def save(self, *args, **kwargs):
        return super(SampleGroupAnalysisResult, self).save(*args, **kwargs)

    def create_field(self, *args, **kwargs):
        field = SampleGroupAnalysisResultField.object.create(analysis_result=self, *args, **kwargs)
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
    analysis_result = models.ForeignKey(SampleAnalysisResult, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        return super(SampleAnalysisResultField, self).save(*args, **kwargs)


class SampleGroupAnalysisResultField(AnalysisResultField):
    """Class representing an analysis result field for a sample group."""
    analysis_result = models.ForeignKey(SampleGroupAnalysisResult, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        return super(SampleGroupAnalysisResultField, self).save(*args, **kwargs)

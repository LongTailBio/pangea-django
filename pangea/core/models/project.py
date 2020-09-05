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

from .sample import Sample
from .analysis_result import SampleGroupAnalysisResult

logger = structlog.get_logger(__name__)


class Project(AutoCreatedUpdatedMixin):
    """This class represents the project model."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(blank=False, unique=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    description = models.TextField(blank=False, default='')
    sample_groups = models.ManyToManyField('SampleGroup', null=True)
    sub_projects = models.ManyToManyField('Project', related_name='super_projects', null=True)

    @property
    def is_public(self):
        public = True
        for grp in self.sample_groups.all():
            public &= grp.is_public
        for proj in self.sub_projects.all():
            public &= proj.is_public
        return public

    def add_sample_group(self, sample_group):
        self.sample_groups.add(sample_group)
        self.save()
        return self

    def add_sub_project(self, sub_project):
        self.sub_projects.add(sub_project)
        self.save()
        return self

    def add_super_project(self, super_project):
        super_project.add_sub_project(self)
        return self

    @classmethod
    def factory(cls, *args, **kwargs):
        proj = cls.objects.create(*args, **kwargs)
        return proj

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return f'<Project name="{self.name}" organization="{self.organization.name}">'

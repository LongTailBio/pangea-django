"""From https://gist.github.com/ertgl/0c26b23ac5482e206a04cb1b13ec3795"""

import structlog

from django.db import models
from django.utils.timezone import now

logger = structlog.get_logger(__name__)


class AutoCreatedUpdatedMixin(models.Model):
    """Django model mixin providing created_at, updated_at fields"""
    created_at = models.DateTimeField(
        unique=False,
        null=True,
        blank=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        unique=False,
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.created_at or (hasattr(self, 'uuid') and not self.uuid):
            self.created_at = now()
            self.updated_at = self.created_at
        else:
            auto_updated_at_is_disabled = kwargs.pop('disable_auto_updated_at', False)
            if not auto_updated_at_is_disabled:
                self.updated_at = now()
        super(AutoCreatedUpdatedMixin, self).save(*args, **kwargs)


class SoftDeleteMixin(models.Model):
    """Django model mixin providing soft deletes."""
    deleted_at = models.DateTimeField(
        unique=False,
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = now()
        kwargs = {
            'using': using,
        }
        if hasattr(self, 'updated_at'):
            kwargs['disable_auto_updated_at'] = True
        self.save(**kwargs)

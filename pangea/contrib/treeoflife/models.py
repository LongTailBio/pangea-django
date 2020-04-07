from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
import uuid
import random
import structlog

from pangea.core.mixins import AutoCreatedUpdatedMixin

from .mixins import (
    MoneraMixin,
    BiotaMixin,
    MicrobeMixin,
)
from .constants import MD2_COLUMN_NAMES



class TaxonName(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    taxon_id = models.TextField(editable=False, db_index=True)
    name = models.TextField(blank=False, db_index=True)
    name_type = models.TextField(blank=False, db_index=True)

    @property
    def tree_node(self):
        return TreeNode.objects.get(taxon_id=self.taxon_id)

    def __str__(self):
        return f'<TreeOfLife::TaxonName name="{self.name}" name_type="{self.name_type}" taxon_id="{self.taxon_id}" uuid="{self.uuid}">'


class TreeNode(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    taxon_id = models.TextField(editable=False, db_index=True)
    parent = models.ForeignKey(
        'TreeNode', on_delete=models.CASCADE, null=True,
        related_name='children'
    )
    rank = models.TextField(blank=False, db_index=True)

    def __str__(self):
        parent_id = self.taxon_id  # root
        if self.taxon_id != '1':
            parent_id = self.parent.taxon_id
        return f'<TreeOfLife::TreeNode taxon_id="{self.taxon_id}" parent_id="{parent_id}" uuid="{self.uuid}"'

    @property
    def canon_name(self):
        return TaxonName.objects.get(taxon_id=self.taxon_id, name_type='scientific name')

    @property
    def all_names(self):
        return TaxonName.objects.filter(taxon_id=self.taxon_id)

    @property
    def annotation(self):
        try:
            for attr in ['bacteria_annotation_set', 'archaea_annotation_set',
                         'fungi_annotation_set', 'virus_annotation_set']:
                if hasattr(self, attr):
                    return getattr(self, attr).all()[0].as_dict()
        except IndexError:  # No annotation present
            return {}

    def ancestors(self, reducer=lambda x: x):
        """Return a list of TreeNodes that are ancestors of this node.

        Start with this node."""
        out = []
        ancestor = self
        while ancestor:
            out.append(reducer(ancestor))
            ancestor = ancestor.parent
        return out

    @classmethod
    def byname(cls, name):
        try:
            return cls.objects.get(taxon_id=name)
        except ObjectDoesNotExist:
            try:
                tid = TaxonName.objects.get(name=name).taxon_id
                return cls.objects.get(taxon_id=tid)
            except:  # TODO broad except
                tid = TaxonName.objects.get(name=name.lower()).taxon_id
                return cls.objects.get(taxon_id=tid)


class MicrobeDirectoryEntry(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    taxon_id = models.TextField(editable=False, db_index=True)

    class Meta:
        abstract = True

    def as_dict(self):
        """Return a dict of annotations."""
        out = {}
        for attr in MD2_COLUMN_NAMES:
            if hasattr(self, attr):
                out[attr] = getattr(self, attr)
        return out


class Bacteria(MicrobeDirectoryEntry, MoneraMixin,):
    tree_node = models.ForeignKey(
        TreeNode,
        on_delete=models.CASCADE,
        related_name='bacteria_annotation_set',
        unique=True
    )


class Archaea(MicrobeDirectoryEntry, MoneraMixin,):
    tree_node = models.ForeignKey(
        TreeNode,
        on_delete=models.CASCADE,
        related_name='archaea_annotation_set',
        unique=True
    )


class Fungi(MicrobeDirectoryEntry, BiotaMixin,):
    tree_node = models.ForeignKey(
        TreeNode,
        on_delete=models.CASCADE,
        related_name='fungi_annotation_set',
        unique=True
    )


class Virus(MicrobeDirectoryEntry, MicrobeMixin,):
    tree_node = models.ForeignKey(
        TreeNode,
        on_delete=models.CASCADE,
        related_name='virus_annotation_set',
        unique=True
    )
    virus_name = models.TextField()
    virus_lineage = models.TextField()
    kegg_genome = models.TextField()
    kegg_disease = models.TextField()
    disease = models.TextField()
    host_name = models.TextField()
    host_lineage = models.TextField()

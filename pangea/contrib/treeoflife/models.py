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

ALLOWED_NAME_TYPES = [
    'acronym',
    'anamorph',
    'authority',
    'blast name',
    'common name',
    'equivalent name',
    'genbank acronym',
    'genbank anamorph',
    'genbank common name',
    'genbank synonym',
    'in-part',
    'includes',
    'scientific name',
    'synonym',
    'teleomorph',
    'type material',
]


class TaxonName(AutoCreatedUpdatedMixin):
    taxon_id = models.TextField(primary_key=True, editable=False, db_index=True)
    name = models.TextField(blank=False, db_index=True)
    name_type = models.TextField(blank=False, db_index=True)


class TreeNode(AutoCreatedUpdatedMixin):
    taxon_id = models.TextField(primary_key=True, editable=False, db_index=True)
    parent = models.ForeignKey('TreeNode')
    rank = models.TextField(blank=False, db_index=True)

    def canon_name(self):
        return TaxonName.objects.get(taxon_id=self.taxon_id, name_type='scientific name').name

    @classmethod
    def byname(cls, name):
        try:
            return cls.objects.get(taxon_id=name)
        except ObjectDoesNotExist:
            tid = TaxonName.objects.get(name=name).taxon_id
            return cls.objects.get(taxon_id=tid)


class MicrobeDirectoryEntry(AutoCreatedUpdatedMixin):
    taxon = models.ForeignKey(TreeNode)


class Monera(MicrobeDirectoryEntry):
    salinity_concentration_range_w_v = models.TextField()
    low_ph = models.TextField()
    high_ph = models.TextField()
    drylands = models.TextField()
    low_productivity = models.TextField()
    gram_stain = models.TextField()
    human_commensal = models.TextField()
    antimicrobial_susceptibility = models.TextField()
    optimal_temperature = models.TextField()
    extreme_environment = models.TextField()
    biofilm_forming = models.TextField()
    optimal_ph = models.TextField()
    animal_pathogen = models.TextField()
    spore_forming = models.TextField()
    pathogenicity = models.TextField()
    plant_pathogen = models.TextField()
    halotolerance = models.TextField()
    psychrophilic = models.TextField()
    radiophilic = models.TextField()


class Bacteria(Monera):
    pass


class Archaea(Monera):
    pass


class Fungi(MicrobeDirectoryEntry):
    salinity_concentration_range_w_v = models.TextField()
    human_commensal = models.TextField()
    antimicrobial_susceptibility = models.TextField()
    optimal_temperature = models.TextField()
    extreme_environment = models.TextField()
    biofilm_forming = models.TextField()
    optimal_ph = models.TextField()
    animal_pathogen = models.TextField()
    spore_forming = models.TextField()
    pathogenicity = models.TextField()
    plant_pathogen = models.TextField()
    halotolerance = models.TextField()


class Virus(MicrobeDirectoryEntry):
    virus_name = models.TextField()
    virus_lineage = models.TextField()
    kegg_genome = models.TextField()
    kegg_disease = models.TextField()
    disease = models.TextField()
    host_name = models.TextField()
    host_lineage = models.TextField()
    gram_stain = models.TextField()
    human_commensal = models.TextField()
    antimicrobial_susceptibility = models.TextField()
    optimal_temperature = models.TextField()
    extreme_environment = models.TextField()
    optimal_ph = models.TextField()
    animal_pathogen = models.TextField()
    spore_forming = models.TextField()
    pathogenicity = models.TextField()
    plant_pathogen = models.TextField()

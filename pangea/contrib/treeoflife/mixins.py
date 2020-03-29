
from django.db import models


class MicrobeMixin(models.Model):
    """Fields available in Bacteria, Archaea, Fungi, & Viruses."""
    human_commensal = models.TextField()
    antimicrobial_susceptibility = models.TextField()
    optimal_temperature = models.TextField()
    extreme_environment = models.TextField()
    optimal_ph = models.TextField()
    animal_pathogen = models.TextField()
    spore_forming = models.TextField()
    pathogenicity = models.TextField()
    plant_pathogen = models.TextField()

    class Meta:
        abstract = True


class BiotaMixin(MicrobeMixin):
    """Fields available in Bacteria, Archaea, & Fungi but not Virus."""
    salinity_concentration_range_w_v = models.TextField()
    biofilm_forming = models.TextField()
    halotolerance = models.TextField()

    class Meta:
        abstract = True


class MoneraMixin(BiotaMixin):
    """Fields available in Bacteria & Archaea, but not Fungi or Virus."""
    low_ph = models.TextField()
    high_ph = models.TextField()
    drylands = models.TextField()
    low_productivity = models.TextField()
    gram_stain = models.TextField()
    psychrophilic = models.TextField()
    radiophilic = models.TextField()

    class Meta:
        abstract = True

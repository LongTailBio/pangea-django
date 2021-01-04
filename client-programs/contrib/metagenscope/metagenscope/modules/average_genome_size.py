
import pandas as pd
from pangea_api import (
    Sample,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
    SampleGroup,
)

from ..base_module import Module
from ..data_utils import (
    group_samples_by_metadata,
    sample_module_field,
)
from .constants import MICROBECENSUS_NAMES
from .parse_utils import parse_generic


def parse_mc_file(filehandle):
    out = {}
    for line in filehandle:
        line = line.strip()
        tkns = line.split()
        if len(tkns) != 2:
            continue
        try:
            out[tkns[0][:-1]] = float(tkns[1])
        except ValueError:
            out[tkns[0][:-1]] = tkns[1]
    return out


def processor(samples):

    def get_ags_distribution(my_samples):
        """Return vector of quartiles of ave genome size."""
        distribution = list(pd.Series({
            sample.name: parse_generic(
                sample_module_field(sample, MICROBECENSUS_NAMES[0], MICROBECENSUS_NAMES[1]),
                parse_mc_file,
            )['average_genome_size']
            for sample in my_samples
        }).quantile([0.1, 0.25, 0.5, 0.75, 0.9]))
        return distribution

    categories, ags_dists = group_samples_by_metadata(samples, group_apply=get_ags_distribution)
    return {
        'categories': categories,
        'distributions': ags_dists,
    }


def sample_has_modules(sample):
    try:
        sample_module_field(sample, MICROBECENSUS_NAMES[0], MICROBECENSUS_NAMES[1])
        return True
    except KeyError:
        return False


class AveGenomeSizeModule(Module):
    """AveGenomeSize AnalysisModule."""
    MIN_SIZE = 3

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'ave_genome_size'

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        samples = [
            sample for sample in grp.get_samples()
            if sample_has_modules(sample)
        ]
        field = grp.analysis_result(
            cls.name(),
            replicate=cls.group_replicate(len(samples))
        ).field(
            'ags',
            data=processor(samples),
        )
        return field

    @classmethod
    def group_has_required_modules(cls, grp: SampleGroup) -> bool:
        count = 0
        for sample in grp.get_samples():
            if sample_has_modules(sample):
                count += 1
            if count >= AveGenomeSizeModule.MIN_SIZE:
                return True
        return False

    @classmethod
    def sample_has_required_modules(cls, sample: Sample) -> bool:
        """Return True iff this sample can be processed."""
        return False

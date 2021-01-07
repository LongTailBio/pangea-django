
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
from .constants import KRAKENUNIQ_NAMES
from .parse_utils import parse_taxa_report, group_taxa_report


def filter_taxa_by_kingdom(taxa_matrix, kingdom, n=20):
    """Return taxa in the given kingdom."""
    if kingdom == 'all_kingdoms':
        cols_to_keep = [col for col in taxa_matrix.columns if '|s__' in col]
        taxa_matrix = taxa_matrix[cols_to_keep]
        taxa_matrix.columns = [col.split('|s__')[-1].split('|')[0] for col in taxa_matrix.columns]
        n = min(n, taxa_matrix.shape[1])
        thresh = 0
        if n > 0:
            thresh = sorted(list(taxa_matrix.mean()), reverse=True)[n - 1]
        taxa_matrix = taxa_matrix[taxa_matrix.mean()[taxa_matrix.mean() >= thresh].index]
        return taxa_matrix
    raise ValueError(f'Kingdom {kingdom} not found.')


def get_group_apply(pangea_group):
    get_taxa_report = group_taxa_report(pangea_group)

    def group_apply(samples):
        out = {}
        for module, field, tool in [KRAKENUNIQ_NAMES]:
            out[tool] = {}
            taxa_matrix = get_taxa_report(samples)
            for kingdom in ['all_kingdoms']:
                taxa_matrix = filter_taxa_by_kingdom(taxa_matrix, kingdom)
                out[tool][kingdom] = {
                    'abundance': taxa_matrix.mean().to_dict(),
                    'prevalence': (taxa_matrix > 0).mean().to_dict(),
                }
        return out
    return group_apply


class TopTaxaModule(Module):
    """TopTaxa AnalysisModule."""

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'top_taxa'

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        group_apply = get_group_apply(grp)
        samples = [
            sample for sample in grp.get_samples()
            if TopTaxaModule.sample_has_required_modules(sample)
        ]
        _, top_taxa = group_samples_by_metadata(
            samples,
            group_apply=group_apply
        )
        field = grp.analysis_result(
            cls.name(),
            replicate=cls.group_replicate(len(samples))
        ).field(
            'top_taxa',
            data={'categories': top_taxa}
        )
        return field

    @classmethod
    def group_has_required_modules(cls, grp: SampleGroup) -> bool:
        for sample in grp.get_samples():
            if cls.sample_has_required_modules(sample):
                return True
        return False

    @classmethod
    def sample_has_required_modules(cls, sample: Sample) -> bool:
        """Return True iff this sample can be processed."""
        try:
            sample_module_field(sample, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1])
            return True
        except KeyError:
            return False

    @classmethod
    def process_sample(cls, sample: Sample) -> SampleAnalysisResultField:
        field = sample.analysis_result(
            cls.name(),
            replicate=cls.sample_replicate()
        ).field(
            'top_taxa',
            data=parse_report(
                sample_module_field(sample, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1])
            )
        )
        return field

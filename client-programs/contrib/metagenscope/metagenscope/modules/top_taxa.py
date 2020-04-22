
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
from .parse_utils import parse_taxa_report


def filter_taxa_by_kingdom(taxa_matrix, kingdom):
    """Return taxa in the given kingdom."""
    if kingdom == 'all_kingdoms':
        return taxa_matrix.filtered_cols(lambda taxa_name, _: 's__' in taxa_name.split('|')[-1])
    raise ValueError(f'Kingdom {kingdom} not found.')


def group_apply(samples):
    out = {}
    for module, field, tool in [KRAKENUNIQ_NAMES]:
        out[tool] = {}
        samples = {
            sample.name: parse_taxa_report(sample_module_field(sample, module, field))
            for sample in samples
        }
        taxa_matrix = pd.DataFrame.from_dict(
            samples,
            orient='index'
        )
        for kingdom in ['all_kingdoms']:
            # kingdom_taxa_matrix = filter_taxa_by_kingdom(taxa_matrix, kingdom)
            out[tool][kingdom] = {
                'abundance': taxa_matrix.mean().to_dict(),
                #'prevalence': kingdom_taxa_matrix.operated_cols(lambda col: col.num_non_zero()),
            }
    return out


class TopTaxaModule(Module):
    """TopTaxa AnalysisModule."""

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'top_taxa'

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        samples = [
            sample for sample in grp.get_samples()
            if TopTaxaModule.sample_has_required_modules(sample)
        ]
        _, top_taxa = group_samples_by_metadata(
            samples,
            group_apply=group_apply
        )
        field = grp.analysis_result(cls.name()).field(
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
        field = sample.analysis_result(cls.name()).field(
            'top_taxa',
            data=parse_report(
                sample_module_field(sample, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1])
            )
        )
        return field

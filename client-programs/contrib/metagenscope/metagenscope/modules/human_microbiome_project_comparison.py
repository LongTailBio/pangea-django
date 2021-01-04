
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
from .constants import HMP_NAMES
from .parse_utils import parse_generic

BODY_SITES = []


def parse_hmp_report(filehandle):
    """Return a dict of <body_site> -> <values>."""
    tbl = pd.read_csv(filehandle)
    observations = tbl.groupby('body_site')
    observations = observations.T.to_dict('list')
    return observations


def group_apply(samples):
    hmp_reports = [
        parse_generic(
            sample_module_field(sample, HMP_NAMES[0], HMP_NAMES[1]),
            parse_hmp_report
        )
        for sample in samples
    ]
    body_sites = {}
    for record in hmp_reports:
        for body_site, observations in record.items():



    out = {}
    for module, field, tool in [KRAKENUNIQ_NAMES]:
        out[tool] = {}

        taxa_matrix = pd.DataFrame.from_dict(
            samples,
            orient='index'
        )
        for kingdom in ['all_kingdoms']:
            taxa_matrix = filter_taxa_by_kingdom(taxa_matrix, kingdom)
            out[tool][kingdom] = {
                'abundance': taxa_matrix.mean().to_dict(),
                'prevalence': (taxa_matrix > 0).mean().to_dict(),
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
        field = grp.analysis_result(
            cls.name(),
            replicate=cls.group_replicate(len(samples))
        ).field(
            'top_taxa',
            data={
                'categories': categories_from_metadata(samples),
                'sites': ['foo', 'bar'],
                'data'
            }
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
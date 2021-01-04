
import pandas as pd
from pangea_api import (
    Sample,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
    SampleGroup,
)

from ..base_module import Module
from ..data_utils import (
    categories_from_metadata,
    sample_module_field,
)
from .constants import KRAKENUNIQ_NAMES
from .parse_utils import parse_taxa_report, group_taxa_report
from .alpha_diversity_metrics import (
    shannon_entropy,
    chao1,
    richness,
)


TAXA_RANKS = ['Any', 'Genus', 'Species']
METRICS = [
    ('Entropy', shannon_entropy),
    ('Richness', richness),
    ('Chao1', chao1),
]
TOOLS = [KRAKENUNIQ_NAMES]


def rank_filter(tbl, rank):
    if rank == 'Genus':
        filters = ('g__', 's__')
    if rank == 'Species':
        filters = ('s__', 't__')
    cols = [
        col for col in tbl.columns
        if (rank == 'Any') or (filters[0] in col and filters[1] not in col)]
    tbl = tbl[cols]
    return tbl


def sample_filter(tbl, samples, cat_name, cat_val):
    samples_in_tbl = set(tbl.index.to_list())
    my_samples = [
        sample.name
        for sample in samples
        if sample.name in samples_in_tbl and (cat_name == 'All' or sample.metadata.get(cat_name, '') == cat_val)
    ]
    my_taxa = tbl.loc[my_samples]
    return my_taxa


def process(samples, grp):
    metadata_categories = categories_from_metadata(samples)
    out = {}
    for module, field, tool in TOOLS:
        taxa_matrix = group_taxa_report(grp)(samples)
        tool_tbl = {'taxa_ranks': TAXA_RANKS, 'by_taxa_rank': {}}
        for rank in TAXA_RANKS:
            rank_tbl = {'by_category_name': {}}
            for cat_name, cat_vals in metadata_categories.items():
                category_list = []
                for cat_val in cat_vals:
                    my_taxa = sample_filter(taxa_matrix, samples, cat_name, cat_val)
                    my_taxa = rank_filter(my_taxa, rank)
                    category_list.append({
                        'metrics': [el[0] for el in METRICS],
                        'category_value': cat_val,
                        'by_metric': {
                            metric: my_taxa.apply(func, axis=1).quantile(
                                [0.1, 0.25, 0.5, 0.75, 0.9]
                            ).to_list()
                            for metric, func in METRICS
                        }
                    })
                rank_tbl['by_category_name'][cat_name] = category_list
            tool_tbl['by_taxa_rank'][rank] = rank_tbl
        out[tool] = tool_tbl
    return out, metadata_categories


class AlphaDiversityModule(Module):
    """TopTaxa AnalysisModule."""
    MIN_SIZE = 3

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'alpha_diversity'

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        samples = [
            sample for sample in grp.get_samples()
            if AlphaDiversityModule.sample_has_required_modules(sample)
        ]
        values, categories = process(samples, grp)
        data = {
            'tool_names': [el[2] for el in TOOLS],
            'categories': categories,
            'by_tool': values,
        }
        field = grp.analysis_result(
            cls.name(),
            replicate=cls.group_replicate(len(samples))
        ).field(
            'alpha_diversity',
            data=data
        )
        return field

    @classmethod
    def group_has_required_modules(cls, grp: SampleGroup) -> bool:
        count = 0
        for sample in grp.get_samples():
            if cls.sample_has_required_modules(sample):
                count += 1
            if count >= AlphaDiversityModule.MIN_SIZE:
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
        raise NotImplementedError()

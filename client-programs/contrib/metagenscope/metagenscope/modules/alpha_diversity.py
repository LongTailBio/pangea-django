
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
from .constants import KRAKEN2_NAMES, FASTKRAKEN2_NAMES
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
TOOLS = [KRAKEN2_NAMES, FASTKRAKEN2_NAMES]


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
        if sample.name in samples_in_tbl and (cat_name == 'All' or sample.mgs_metadata.get(cat_name, '') == cat_val)
    ]
    my_taxa = tbl.loc[my_samples]
    return my_taxa


def process(samples, grp, tools):
    metadata_categories = categories_from_metadata(samples)
    out = {}
    for _, _, tool, module, field in tools:
        taxa_matrix = group_taxa_report(grp, module_name=module, field_name=field)(samples)
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
                            ).fillna(0).to_list()
                            for metric, func in METRICS
                        }
                    })
                rank_tbl['by_category_name'][cat_name] = category_list
            tool_tbl['by_taxa_rank'][rank] = rank_tbl
        out[tool] = tool_tbl
    return out, metadata_categories


def sample_has_modules(sample):
    """Return True iff sample has at least one module."""
    tool_list = []
    for tool in TOOLS:
        try:
            sample_module_field(sample, tool[0], tool[1])
            tool_list.append(tool)
        except KeyError:
            continue
    return len(tool_list) > 0, sample, tool_list


class AlphaDiversityModule(Module):
    """TopTaxa AnalysisModule."""
    MIN_SIZE = 3

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'alpha_diversity'

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        sample_modules = [
            sample_has_modules(sample)
            for sample in grp.get_samples()
        ]
        tool_counts, samples = {}, []
        for has_modules, sample, tools in sample_modules:
            if not has_modules:
                continue
            for tool in tools:
                tool_counts[tool] = 1 + tool_counts.get(tool, 0)
            samples.append(sample)
        tools = [tool for tool, count in tool_counts.items() if count > cls.MIN_SIZE]
        values, categories = process(samples, grp, tools)
        data = {
            'tool_names': [el[2] for el in tools],
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
        return sample_has_modules(sample)[0]

    @classmethod
    def process_sample(cls, sample: Sample) -> SampleAnalysisResultField:
        raise NotImplementedError()

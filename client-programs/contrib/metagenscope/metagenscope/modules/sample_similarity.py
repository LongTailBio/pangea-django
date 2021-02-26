
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
    scrub_category_val,
    group_samples_by_metadata,
    sample_module_field,
)
from ..remote_utils import download_s3_file
from .constants import KRAKEN2_NAMES, FASTKRAKEN2_NAMES
from .parse_utils import (
    parse_taxa_report,
    umap,
    proportions,
    group_taxa_report,
)

TOOLS = [KRAKEN2_NAMES, FASTKRAKEN2_NAMES]


def taxa_tool_umap(samples, grp, module, field):
    """Run UMAP for tool results stored as 'taxa' property."""
    taxa_matrix = group_taxa_report(grp, module_name=module, field_name=field)(samples)
    reduced = umap(taxa_matrix).to_dict(orient='index')
    return reduced


def process_one_tool(samples, sample_recs, grp, tool):
    for sample_name, coords in taxa_tool_umap(samples, grp, tool[3], tool[4]).items():
        sample_recs[sample_name][f'{tool[2]}_x'] = coords['C0']
        sample_recs[sample_name][f'{tool[2]}_y'] = coords['C1']


def processor(samples, grp, tools):
    """Combine Sample Similarity components."""
    out = {
        'categories': categories_from_metadata(samples),
        'tools': {
            tool[2]: {
                'x_label': tool[2] + '_x',
                'y_label': tool[2] + '_y',
            }
            for tool in tools
        },
    }
    sample_recs = {}
    for sample in samples:
        sample_recs[sample.name] = {'name': sample.name}
        for key, val in sample.mgs_metadata.items():
            if key in ['name']:
                continue
            sample_recs[sample.name][key] = val
        sample_recs[sample.name]['All'] = 'All'

    tools_failed = 0
    for tool in tools:
        try:
            process_one_tool(samples, sample_recs, grp, tool)
        except Exception as e:
            print(e)
            tools_failed += 1
            continue
    assert tools_failed < len(tools)
    out['data_records'] = list(sample_recs.values())
    return out


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


class SampleSimilarityModule(Module):
    """SampleSimilarity AnalysisModule."""
    MIN_SIZE = 10

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'sample_similarity'

    @classmethod
    def version(self):
        return 'v3.2.2'

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
        tools = [tool for tool, count in tool_counts.items() if count >= cls.MIN_SIZE]
        meta = pd.DataFrame.from_dict(
            {sample.name: sample.mgs_metadata for sample in samples},
            orient='index'
        ).fillna('Unknown')
        for sample in samples:
            sample.mgs_metadata = meta.loc[sample.name].to_dict()
        return grp.analysis_result(
            cls.name(),
            replicate=cls.group_replicate(len(samples))
        ).field(
            'dim_reduce',
            data=processor(samples, grp, tools),
        )

    @classmethod
    def group_has_required_modules(cls, grp: SampleGroup) -> bool:
        count = 0
        for sample in grp.get_samples():
            if sample_has_modules(sample):
                count += 1
            if count >= SampleSimilarityModule.MIN_SIZE:
                return True
        return False

    @classmethod
    def sample_has_required_modules(cls, sample: Sample) -> bool:
        """Individual samples cannot be processed"""
        return False


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
from .constants import KRAKENUNIQ_NAMES
from .parse_utils import (
    parse_taxa_report,
    umap,
    proportions,
    group_taxa_report,
)


def taxa_tool_umap(samples, grp, module, field):
    """Run UMAP for tool results stored as 'taxa' property."""
    taxa_matrix = group_taxa_report(grp)(samples)
    reduced = umap(taxa_matrix).to_dict(orient='index')
    return reduced


def processor(samples, grp):
    """Combine Sample Similarity components."""
    data_records = []
    sample_map = {sample.name: sample.metadata for sample in samples}
    for sample_name, coords in taxa_tool_umap(samples, grp, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1]).items():
        rec = {
            'name': sample_name,
            f'{KRAKENUNIQ_NAMES[2]}_x': coords['C0'],
            f'{KRAKENUNIQ_NAMES[2]}_y': coords['C1'],
        }
        for key, val in sample_map[sample_name].items():
            if key in ['name']:
                continue
            rec[key] = val
        rec['All'] = 'All'
        data_records.append(rec)
    return {
        'categories': categories_from_metadata(samples),
        'tools': {
            KRAKENUNIQ_NAMES[2]: {
                'x_label': KRAKENUNIQ_NAMES[2] + '_x',
                'y_label': KRAKENUNIQ_NAMES[2] + '_y',
            }
        },
        'data_records': data_records,
    }


def sample_has_modules(sample):
    try:
        sample_module_field(sample, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1])
        return True
    except KeyError:
        return False


class SampleSimilarityModule(Module):
    """SampleSimilarity AnalysisModule."""
    MIN_SIZE = 10

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'sample_similarity'

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        samples = [
            sample for sample in grp.get_samples()
            if sample_has_modules(sample)
        ]
        meta = pd.DataFrame.from_dict(
            {sample.name: sample.metadata for sample in samples},
            orient='index'
        ).fillna('Unknown')
        for sample in samples:
            sample.metadata = meta.loc[sample.name].to_dict()
        return grp.analysis_result(
            cls.name(),
            replicate=cls.group_replicate(len(samples))
        ).field(
            'dim_reduce',
            data=processor(samples, grp),
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

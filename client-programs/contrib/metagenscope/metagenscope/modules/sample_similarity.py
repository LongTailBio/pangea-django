
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
)


def taxa_tool_umap(samples, module, field):
    """Run UMAP for tool results stored as 'taxa' property."""
    samples = pd.DataFrame.from_dict({
        sample.name: parse_taxa_report(sample_module_field(sample, module, field))
        for sample in samples
    }, orient='index').fillna(0)
    samples = proportions(samples)
    reduced = umap(samples).to_dict()
    return reduced


def processor(samples):
    """Combine Sample Similarity components."""
    return {
        'categories': categories_from_metadata(samples),
        'tools': {
            KRAKENUNIQ_NAMES[2]: taxa_tool_umap(samples, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1]),
        },
        'data_records': {
            sample.name: {
                category_name: scrub_category_val(category_value)
                for category_name, category_value in sample.metadata.items()
            }
            for sample in samples
        },
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
        return grp.analysis_result(cls.name()).field(
            'dim_reduce',
            data=processor(samples),
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

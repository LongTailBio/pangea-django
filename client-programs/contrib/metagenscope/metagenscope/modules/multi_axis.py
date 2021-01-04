
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
    group_samples_by_metadata,
    sample_module_field,
)
from .constants import (
    KRAKENUNIQ_NAMES,
    MICROBECENSUS_NAMES,
)
from .average_genome_size import parse_mc_file
from .alpha_diversity_metrics import (
    shannon_entropy,
    chao1,
    richness,
)
from .parse_utils import (
    parse_taxa_report,
    parse_generic,
    umap,
    run_pca,
    group_taxa_report,
)

TOOLS = [KRAKENUNIQ_NAMES] #, MICROBECENSUS_NAMES]


def taxa_axes(samples, grp):
    taxa_matrix = group_taxa_report(grp)(samples)
    pca = run_pca(taxa_matrix, n_comp=3)
    out = {
        f'{KRAKENUNIQ_NAMES[2]} Chao1': {'vals': taxa_matrix.apply(chao1, axis=1).to_dict()},
        f'{KRAKENUNIQ_NAMES[2]} Richness': {'vals': taxa_matrix.apply(richness, axis=1).to_dict()},
        f'{KRAKENUNIQ_NAMES[2]} Entropy': {'vals': taxa_matrix.apply(shannon_entropy, axis=1).to_dict()},
        f'{KRAKENUNIQ_NAMES[2]} UMAP-1D': {'vals': umap(taxa_matrix, n_components=1)['C0'].to_dict()},
        f'{KRAKENUNIQ_NAMES[2]} PC-1': {'vals': pca['C0'].to_dict()},
        f'{KRAKENUNIQ_NAMES[2]} PC-2': {'vals': pca['C1'].to_dict()},
        f'{KRAKENUNIQ_NAMES[2]} PC-3': {'vals': pca['C2'].to_dict()},
    }
    return out


def make_axes(samples, grp):
    out = taxa_axes(samples, grp)
    # out['Ave. Genome Size'] = {'vals': pd.Series({
    #     sample.name: parse_generic(
    #         sample_module_field(sample, MICROBECENSUS_NAMES[0], MICROBECENSUS_NAMES[1]),
    #         parse_mc_file,
    #     )['average_genome_size']
    #     for sample in samples
    # }).to_dict()}
    return out


def sample_has_modules(sample):
    has_all = True
    for module_name, field, _ in TOOLS:
        try:
            sample_module_field(sample, module_name, field)
        except KeyError:
            has_all = False
    return has_all


class MultiAxisModule(Module):
    """TopTaxa AnalysisModule."""
    MIN_SIZE = 3

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'multi_axis'

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        samples = [
            sample for sample in grp.get_samples()
            if sample_has_modules(sample)
        ]
        meta = {}
        for sample in samples:
            meta[sample.name] = sample.metadata
            meta[sample.name]['All'] = 'All'
        data = {
            'axes': make_axes(samples, grp),
            'categories': categories_from_metadata(samples),
            'metadata': meta,
        }
        field = grp.analysis_result(
            cls.name(),
            replicate=cls.group_replicate(len(samples))
        ).field(
            'multi_axis',
            data=data
        )
        return field

    @classmethod
    def group_has_required_modules(cls, grp: SampleGroup) -> bool:
        count = 0
        for sample in grp.get_samples():
            if sample_has_modules(sample):
                count += 1
            if count >= cls.MIN_SIZE:
                return True
        return False

    @classmethod
    def sample_has_required_modules(cls, sample: Sample) -> bool:
        """Return True iff this sample can be processed."""
        return False


import pandas as pd
import math
from scipy.stats import mannwhitneyu
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
    categories_from_metadata,
)
from .constants import KRAKEN2_NAMES, FASTKRAKEN2_NAMES
from .parse_utils import group_taxa_report, parse_taxa_report, proportions

TOOLS = [KRAKEN2_NAMES, FASTKRAKEN2_NAMES]
MIN_GRP_SIZE = 6


class VolcanoError(Exception):
    pass


def stats(col, cat1_samples, cat2_samples):
    cat1, cat2 = col[cat1_samples] + 0.0000001, col[cat2_samples] + 0.0000001
    _, pval = mannwhitneyu(cat1, cat2, alternative=None)
    lratio = math.log2(cat1.mean() / cat2.mean())
    return pd.Series({
        'xval': lratio,
        'yval': pval,
        'zval': col.mean(),
    })


def pval_hist(pvals, bin_width=0.05):
    """Return a histogram of pvalues."""
    nbins = int(1 / bin_width + 0.5)
    bins = {bin_width * i: 0
            for i in range(nbins)}
    for pval in pvals:
        for bin_start in bins:
            bin_end = bin_start + bin_width
            if bin_start <= pval < bin_end:
                bins[bin_start] += 1
                break
    pts = [{'name': f'histo_{bin_start}', 'xval': bin_start, 'yval': nps}
           for bin_start, nps in bins.items()]
    return pts


def scatter(taxa, samples, cat_name, cat_val):
    cat1_samples = {
        sample.name for sample in samples
        if sample.mgs_metadata.get(cat_name, '') == cat_val
    }
    cat2_samples = {
        sample.name for sample in samples
        if sample.name not in cat1_samples
    }
    if len(cat2_samples) < MIN_GRP_SIZE or len(cat1_samples) < MIN_GRP_SIZE:
        raise VolcanoError('group too small.')
    taxa = taxa[taxa.columns[taxa.sum() > 0]]
    pts = taxa.apply(lambda col: stats(col, cat1_samples, cat2_samples))
    pts = pts.T
    pts['name'] = pts.index.map(lambda el: el.split('|')[-1].split('__')[1])
    pvals = pval_hist(pts['yval'])
    pts['yval'] = pts['yval'].map(lambda x: -math.log2(x))
    return pts.to_dict('records'), pvals


def process(grp, samples, tools, max_taxa=0):
    metadata_categories = categories_from_metadata(samples)
    out = {}
    for _, _, tool, module, field in tools:
        taxa_matrix = group_taxa_report(grp, module_name=module, field_name=field)(samples)
        if max_taxa and taxa_matrix.shape[1] > max_taxa:
            taxa = taxa_matrix.mean().sort_values(ascending=False).index.to_list()[:max_taxa]
            taxa_matrix = taxa_matrix[taxa]
        tool_tbl = {'tool_categories': {}}
        for cat_name, cat_vals in metadata_categories.items():
            cat_tbl = {}
            for cat_val in cat_vals:
                try:
                    val_tbl = {}
                    pts, pvals = scatter(taxa_matrix, samples, cat_name, cat_val)
                    val_tbl['pval_histogram'] = pvals
                    val_tbl['scatter_plot'] = pts
                    cat_tbl[cat_val] = val_tbl
                except VolcanoError:
                    pass
            if cat_tbl:
                tool_tbl['tool_categories'][cat_name] = cat_tbl
        if tool_tbl['tool_categories']:
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


class VolcanoModule(Module):
    """TopTaxa AnalysisModule."""
    MIN_SIZE = 12
    MAX_TAXA = 100

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'volcano'

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
        volcano, cats = process(grp, samples, tools, cls.MAX_TAXA)
        if not volcano:
            raise VolcanoError('No differentiable group found')
        data = {
            'categories': cats,
            'tools': volcano,
        }
        field = grp.analysis_result(
            cls.name(),
            replicate=cls.group_replicate(len(samples))
        ).field(
            'volcano',
            data=data
        )
        return field

    @classmethod
    def group_has_required_modules(cls, grp: SampleGroup) -> bool:
        count = 0
        for sample in grp.get_samples():
            if sample_has_modules(sample)[0]:
                count += 1
            if count >= cls.MIN_SIZE:
                return True
        return False

    @classmethod
    def sample_has_required_modules(cls, sample: Sample) -> bool:
        """Return True iff this sample can be processed."""
        return False

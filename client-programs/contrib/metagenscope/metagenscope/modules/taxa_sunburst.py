
import pandas as pd
from pangea_api import (
    Sample,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
    SampleGroup,
)
import logging

from ..base_module import Module
from ..data_utils import sample_module_field
from .constants import FASTKRAKEN2_NAMES
from .parse_utils import format_taxon_name

logger = logging.getLogger(__name__)


def parse_taxa_report(report: SampleAnalysisResultField, **kwargs):
    local_path = report.download_file()
    try:
        return _parse_taxa_report(local_path, **kwargs)
    except Exception:
        logger.debug(f'[ParseTaxaReport] failed to parse {local_path}')
        raise


def _parse_taxa_report(local_path, **kwargs):
    """Return a dict of taxa_name to read_counts."""
    out, abundance_sum = {}, 0
    with open(local_path) as taxa_file:
        for line_num, line in enumerate(taxa_file):
            line = line.strip()
            tkns = line.split('\t')
            if not line or len(tkns) < 2:
                continue
            if len(tkns) == 2:
                taxon = tkns[0]
                taxon = taxon.split('|')[-1]
                abundance = float(tkns[1])
            elif len(tkns) == 6:
                taxon = tkns[5].strip()
                taxon_rank = tkns[3].strip().lower()
                if len(taxon_rank) > 1:
                    continue
                taxon = f'{taxon_rank}__{taxon}'
                abundance = float(tkns[1])
            else:
                if line_num == 0:
                    continue
                taxon = tkns[1]
                abundance = float(tkns[3])
            if (not kwargs.get('species_only', False)) or ('s__' in taxon):
                out[taxon] = abundance
                abundance_sum += abundance
    if kwargs.get('normalize', False):
        out = {k: v / abundance_sum for k, v in out.items()}
    if kwargs.get('minimum_abundance', 0):
        out = {k: v for k, v in out.items() if v >= kwargs['minimum_abundance']}
    return out


def get_total(taxa_list, delim):
    """Return the total abundance in the taxa list.
    This is not the sum b/c taxa lists are trees, implicitly.
    """
    total = 0.001  # psuedocount
    for taxon, abund in taxa_list.items():
        tkns = taxon.split(delim)
        if len(tkns) == 1:
            total += abund
    return total


def get_taxa_tokens(taxon, delim, tkn_delim='__'):
    """Return a list of cleaned tokens."""
    tkns = taxon.split(delim)
    tkns = [tkn.split(tkn_delim)[-1] for tkn in tkns]
    return tkns


def reduce_taxa_list(taxa_list, delim='|'):
    """Return a tree built from a taxa list."""
    factor = 100 / get_total(taxa_list, delim)
    nodes = {
        'root': {
            'id': 'root',
            'name': 'Root',
            'parent': '',
            'value': 100,
        }
    }
    for taxon, abund in taxa_list.items():
        tkns = get_taxa_tokens(taxon, delim)
        for i, taxon in enumerate(tkns):
            if taxon not in nodes:
                nodes[taxon] = {
                    'name': format_taxon_name(taxon),
                    'id': taxon,
                    'parent': 'root' if i == 0 else tkns[i - 1],
                }
        proportion = factor * abund
        if proportion >= 0.01:
            nodes[tkns[-1]]['value'] = proportion
        else:
            del nodes[tkns[-1]]
    return list(nodes.values())


def trees_from_sample(sample):
    """Build taxa trees for a given sample."""

    krakenhll = reduce_taxa_list(
        parse_taxa_report(
            sample_module_field(sample, FASTKRAKEN2_NAMES[0], FASTKRAKEN2_NAMES[1])
        )
    )
    return {
        FASTKRAKEN2_NAMES[2]: krakenhll,
    }


class TaxaSunburstModule(Module):
    """TopTaxa AnalysisModule."""

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'taxa_tree'

    @classmethod
    def sample_has_required_modules(cls, sample: Sample) -> bool:
        """Return True iff this sample can be processed."""
        try:
            sample_module_field(sample, FASTKRAKEN2_NAMES[0], FASTKRAKEN2_NAMES[1])
            return True
        except KeyError:
            return False

    @classmethod
    def process_sample(cls, sample: Sample) -> SampleAnalysisResultField:
        data = trees_from_sample(sample)
        field = sample.analysis_result(
            cls.name(),
            replicate=cls.sample_replicate()
        ).field(
            'sunburst',
            data=data
        )
        return field

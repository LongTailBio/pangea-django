
import pandas as pd
from pangea_api import (
    Sample,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
    SampleGroup,
)

from ..base_module import Module
from ..data_utils import sample_module_field
from .constants import KRAKENUNIQ_NAMES
from .parse_utils import parse_taxa_report, format_taxon_name


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
            sample_module_field(sample, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1])
        )
    )
    return {
        KRAKENUNIQ_NAMES[2]: krakenhll,
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
            sample_module_field(sample, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1])
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

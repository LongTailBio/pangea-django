
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
from .parse_utils import parse_taxa_report


def get_total(taxa_list, delim):
    """Return the total abundance in the taxa list.
    This is not the sum b/c taxa lists are trees, implicitly.
    """
    total = 0
    for taxon, abund in taxa_list.items():
        tkns = taxon.split(delim)
        if len(tkns) == 1:
            total += abund
    return total


def convert_children_to_list(taxa_tree):
    """Convert a dictionary of children to a list, recursively."""
    children = taxa_tree['children']
    taxa_tree['children'] = [convert_children_to_list(child)
                             for child in children.values()]
    return taxa_tree


def get_taxa_tokens(taxon, delim, tkn_delim='__'):
    """Return a list of cleaned tokens."""
    tkns = taxon.split(delim)
    tkns = [tkn.split(tkn_delim)[-1] for tkn in tkns]
    return tkns


def recurse_tree(tree, tkns, i, leaf_size):
    """Return a recursively built tree."""
    is_leaf = (i + 1) == len(tkns)
    tkn = tkns[i]

    try:
        tree['children'][tkn]
    except KeyError:
        tree['children'][tkn] = {
            'name': tkn,
            'parent': 'root',
            'size': 0,
            'children': {},
        }
        if i > 0:
            tree['children'][tkn]['parent'] = tkns[i - 1]
        if is_leaf:
            tree['children'][tkn]['size'] = leaf_size
    if is_leaf:
        return tree['children'][tkn]
    return recurse_tree(tree['children'][tkn], tkns, i + 1, leaf_size)


def reduce_taxa_list(taxa_list, delim='|'):
    """Return a tree built from a taxa list."""
    factor = 100 / get_total(taxa_list, delim)
    taxa_tree = {
        'name': 'root',
        'parent': None,
        'size': 100,
        'children': {}
    }
    for taxon, abund in taxa_list.items():
        tkns = get_taxa_tokens(taxon, delim)
        recurse_tree(taxa_tree, tkns, 0, factor * abund)
    taxa_tree = convert_children_to_list(taxa_tree)
    return taxa_tree


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
        field = sample.analysis_result(cls.name()).field(
            'sunburst',
            data=data
        )
        return field

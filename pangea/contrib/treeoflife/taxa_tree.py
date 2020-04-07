import pandas as pd

from os import environ
from os.path import join, dirname
import gzip

from .models import (
    TaxonName,
    TreeNode,
)


NCBI_DELIM = '\t|'  # really...
NAMES_ENV_VAR = 'CAPALYZER_NCBI_NAMES'
NODES_ENV_VAR = 'CAPALYZER_NCBI_NODES'
NAMES_DEF = join(dirname(__file__), 'ncbi_tree/names.dmp.gz')
NODES_DEF = join(dirname(__file__), 'ncbi_tree/nodes.dmp.gz')

RANKS = ['species', 'genus', 'family', 'order', 'class', 'phylum', 'superkingdom']


class TaxaTree:

    @staticmethod
    def ancestors(taxon):
        """Return a list of all ancestors of the taxon starting with the taxon itself."""
        node = TreeNode.byname(taxon)
        parents = [node.canon_name.name]
        while node.parent.canon_name.name != 'root':
            parents.append(node.parent.canon_name.name)
            node = node.parent
        return parents

    @staticmethod
    def ranked_ancestors(taxon):
        """Return a dict of all ancestors of the taxon starting with the taxon itself.
        Keys of the dict are taxon ranks
        """
        node = TreeNode.byname(taxon)
        parents = {node.rank: node.canon_name.name}
        while node.parent.canon_name.name != 'root':
            parents[node.parent.rank] = node.parent.canon_name.name
            node = node.parent
        return parents

    @staticmethod
    def ancestor_rank(rank, taxon, default=None):
        """Return the ancestor of taxon at the given rank."""
        node = TreeNode.byname(taxon)
        while node.parent.canon_name.name != 'root':
            if rank == node.parent.rank:
                return node.parent.canon_name.name
            node = node.parent
        if not default:
            raise KeyError(f'{rank} for taxa {taxon} not found.')
        return default

    @staticmethod
    def get_taxon_parent_lists(taxa):
        """Return a pair of lists giving the name of each taxon and its parent.

        Give an empty string as the parent of the root.

        This function is used to prepare data for a Plotly suburst plot.
        """
        queue = list(taxa)[::1]  # deep copy
        added = set()
        taxon_list, parent_list = [], []
        while queue:
            taxon = queue.pop()
            if taxon in added:
                continue
            parent = ''
            if taxon != 'root':
                parent = TreeNode.byname(taxon).parent.canon_name.name
            taxon_list.append(taxon)
            parent_list.append(parent)
            added.add(taxon)
            if taxon != 'root':
                queue.append(parent)
        return taxon_list, parent_list

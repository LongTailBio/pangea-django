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
        queue = [TreeNode.byname(taxon) for taxon in taxa]
        added = set()
        taxon_list, parent_list = [], []
        while queue:
            node = queue.pop()
            if node.taxon_id in added:
                continue
            node_name = node.canon_name.name
            if node_name in added:
                continue
            taxon_list.append(node_name)
            parent_name = ''
            if not node.is_root:
                parent_node = node.parent
                parent_name = parent_node.canon_name.name
                while parent_name == node_name:
                    parent_node = parent_node.parent
                    parent_name = ''
                    if parent_node:
                        parent_name = parent_node.canon_name.name
                queue.append(node.parent)
            parent_list.append(parent_name)
            added.add(node.taxon_id)
            added.add(node_name)

        return taxon_list, parent_list

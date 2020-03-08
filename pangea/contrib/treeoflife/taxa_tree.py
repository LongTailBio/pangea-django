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

    def ancestors(self, taxon):
        """Return a list of all ancestors of the taxon starting with the taxon itself."""
        node = TreeNode.byname(taxon)
        parents = [node.canon_name()]
        while node.parent.canon_name() != 'root':
            parents.append(node.parent.canon_name())
            node = node.parent
        return parents

    def ranked_ancestors(self, taxon):
        """Return a dict of all ancestors of the taxon starting with the taxon itself.
        Keys of the dict are taxon ranks
        """
        node = TreeNode.byname(taxon)
        parents = {node.rank: node.canon_name()}
        while node.parent.canon_name() != 'root':
            parents[node.parent.rank] = node.parent.canon_name()
            node = node.parent
        return parents

    def ancestor_rank(self, rank, taxon, default=None):
        """Return the ancestor of taxon at the given rank."""
        parent_num = self.parent_map[self._node(taxon)]
        node = TreeNode.byname(taxon)
        while node.parent.canon_name() != 'root':
            if rank == node.parent.rank:
                return node.parent.canon_name()
            node = node.parent
        if not default:
            raise KeyError(f'{rank} for taxa {taxon} not found.')
        return default

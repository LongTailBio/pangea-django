
import gzip
import sys
from time import time
from os import environ
from os.path import join, dirname
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from pangea.contrib.treeoflife.models import (
    TaxonName,
    TreeNode,
)

NCBI_DELIM = '\t|'  # really...
NAMES_ENV_VAR = 'PANGEA_TREEOFLIFE_NCBI_NAMES'
NODES_ENV_VAR = 'PANGEA_TREEOFLIFE_NCBI_NODES'
TREEOFLIFE_DIR = dirname(dirname(__file__))
NAMES_DEF = join(TREEOFLIFE_DIR, 'ncbi_tree/names.dmp.gz')
NODES_DEF = join(TREEOFLIFE_DIR, 'ncbi_tree/nodes.dmp.gz')


def tokenize(filehandle):
    for i, line in enumerate(filehandle):
        line = line.decode('utf-8')
        tkns = [tkn.strip() for tkn in line.strip().split(NCBI_DELIM)]
        yield i, tkns


class TaxaTree:

    def __init__(self):
        self.rank_map = {}
        self.parent_map = {}
        self.nodes_created = {}

    def create_node_in_db(self, taxon_id):
        if taxon_id in self.nodes_created:
            return
        parent_id = self.parent_map[taxon_id]
        if parent_id and parent_id not in self.nodes_created:
            try:
                self.create_node_in_db(parent_id)
            except KeyError:
                parent_id = '1'  # if parent is missing assign the root as the parent

        parent = self.nodes_created[parent_id] if parent_id else None
        node = TreeNode(
            taxon_id=taxon_id,
            parent=parent,
            rank=self.rank_map[taxon_id],
        )
        node.save()
        self.nodes_created[taxon_id] = node

    def create_all_nodes_in_db(self):
        for i, taxon_id in enumerate(self.rank_map.keys()):
            self.create_node_in_db(taxon_id)

    def add_node(self, taxon_id, parent_id, rank):
        self.rank_map[taxon_id] = rank
        if parent_id == taxon_id:  # NCBI has a self loop at the root
            parent_id = None
        self.parent_map[taxon_id] = parent_id


def add_nodes(nodes_filename):
    tree = TaxaTree()
    TreeNode.objects.all().delete()
    with gzip.open(nodes_filename) as nodes_file:
        for i, tkns in tokenize(nodes_file):
            taxon_id, parent_id, rank = tkns[0], tkns[1], tkns[2]
            if rank == 'no rank' and int(taxon_id) > 1000:
                continue  # should filter out strains and lower
            if i > (2 * 1000):
                break
            tree.add_node(taxon_id, parent_id, rank)
    tree.create_all_nodes_in_db()
    return tree


def add_names(tree, names_filename):
    """Add names from names_filename to database."""
    nodes_created = set(tree.nodes_created.keys())
    assert '562' in nodes_created
    TaxonName.objects.all().delete()
    with gzip.open(names_filename) as names_file:
        batch = []
        for i, tkns in tokenize(names_file):
            if i > (20 * 1000):
                break
            taxon_id = tkns[0]
            if taxon_id not in nodes_created:
                continue
            batch.append(TaxonName(taxon_id=taxon_id, name=tkns[1], name_type=tkns[3]))
            if len(batch) == 1000:
                TaxonName.objects.bulk_create(batch)
                batch = []
        TaxonName.objects.bulk_create(batch)


def populate_test_db():
    try:
        TaxonName.objects.get(taxon_id='1')
        return
    except ObjectDoesNotExist:
        pass
    names_filename = environ.get(NAMES_ENV_VAR, NAMES_DEF)
    nodes_filename = environ.get(NODES_ENV_VAR, NODES_DEF)
    tree = add_nodes(nodes_filename)
    add_names(tree, names_filename)

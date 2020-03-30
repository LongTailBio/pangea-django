
import gzip
import sys
from time import time
from os import environ
from os.path import join, dirname
from django.core.management.base import BaseCommand
from pangea.contrib.treeoflife.models import (
    TaxonName,
    TreeNode,
)
from pangea.contrib.treeoflife.utils import populate_md2

NCBI_DELIM = '\t|'  # really...
NAMES_ENV_VAR = 'PANGEA_TREEOFLIFE_NCBI_NAMES'
NODES_ENV_VAR = 'PANGEA_TREEOFLIFE_NCBI_NODES'
TREEOFLIFE_DIR = dirname(dirname(dirname(__file__)))
NAMES_DEF = join(TREEOFLIFE_DIR, 'ncbi_tree/names.dmp.gz')
NODES_DEF = join(TREEOFLIFE_DIR, 'ncbi_tree/nodes.dmp.gz')


def tokenize(filehandle):
    for i, line in enumerate(filehandle):
        line = line.decode('utf-8')
        tkns = [tkn.strip() for tkn in line.strip().split(NCBI_DELIM)]
        yield i, tkns


def add_names(names_filename, N=1000):
    """Add names from names_filename to database.

    Note takes up to ~30 mintues to run for the full file.
    """
    start_time = time()
    TaxonName.objects.all().delete()
    with gzip.open(names_filename) as names_file:
        batch = []
        for i, tkns in tokenize(names_file):
            if i % N == 0:
                elapsed = int(time() - start_time)
                sys.stderr.write(f'\rAdded {i:,} taxa to database in {elapsed:,} seconds')
            batch.append(TaxonName(taxon_id=tkns[0], name=tkns[1], name_type=tkns[2]))
            if len(batch) == N:
                TaxonName.objects.bulk_create(batch)
                batch = []
        TaxonName.objects.bulk_create(batch)
        elapsed = int(time() - start_time)
        sys.stderr.write(f'\rAdded {i:,} taxa to database in {elapsed:,} seconds\n')


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
            self.create_node_in_db(parent_id)
        parent = self.nodes_created[parent_id] if parent_id else None
        node = TreeNode(
            taxon_id=taxon_id,
            parent=parent,
            rank=self.rank_map[taxon_id],
        )
        node.save()
        self.nodes_created[taxon_id] = node

    def create_all_nodes_in_db(self):
        start_time = time()
        for i, taxon_id in enumerate(self.rank_map.keys()):
            if i % (1000) == 0:
                elapsed = int(time() - start_time)
                sys.stderr.write(f'\rAdded {i:,} tree nodes to database in {elapsed:,} seconds')
            self.create_node_in_db(taxon_id)
        elapsed = int(time() - start_time)
        sys.stderr.write(f'\rAdded {i:,} tree nodes to database in {elapsed:,} seconds\n')

    def add_node(self, taxon_id, parent_id, rank):
        self.rank_map[taxon_id] = rank
        if parent_id == taxon_id:  # NCBI has a self loop at the root
            parent_id = None
        self.parent_map[taxon_id] = parent_id


def add_nodes(nodes_filename):
    tree = TaxaTree()
    TreeNode.objects.all().delete()
    with gzip.open(nodes_filename) as nodes_file:
        for _, tkns in tokenize(nodes_file):
            taxon_id, parent_id, rank = tkns[0], tkns[1], tkns[3]
            tree.add_node(taxon_id, parent_id, rank)
    sys.stderr.write(f'Parsed tree file.\n')
    tree.create_all_nodes_in_db()


class Command(BaseCommand):
    help = 'Populate the taxonomic tree with the NCBI tree'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-names',
            action='store_true',
            help='Do not add names',
        )
        parser.add_argument(
            '--no-nodes',
            action='store_true',
            help='Do not add nodes',
        )
        parser.add_argument(
            '--no-md2',
            action='store_true',
            help='Do not add microbe dir annotations',
        )

    def handle(cls, *args, **kwargs):
        """Populate database tables with taxonomic info."""
        names_filename = environ.get(NAMES_ENV_VAR, NAMES_DEF)
        nodes_filename = environ.get(NODES_ENV_VAR, NODES_DEF)
        N = 10 * 1000

        if not kwargs['no_names']:
            add_names(names_filename)
        if not kwargs['no_nodes']:
            add_nodes(nodes_filename)
        if not kwargs['no_md2']:
            populate_md2()

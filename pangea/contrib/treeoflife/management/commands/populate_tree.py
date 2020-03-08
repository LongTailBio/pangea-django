
import gzip

from os import environ
from os.path import join, dirname
from django.core.management.base import BaseCommand, CommandError
from polls.models import Question as Poll
from pangea.contrib.treeoflife.models import (
    TaxonName,
    TreeNode,
)

NCBI_DELIM = '\t|'  # really...
NAMES_ENV_VAR = 'PANGEA_TREEOFLIFE_NCBI_NAMES'
NODES_ENV_VAR = 'PANGEA_TREEOFLIFE_NCBI_NODES'
TREEOFLIFE_DIR = dirname(dirname(dirname(__file__)))
NAMES_DEF = join(TREEOFLIFE_DIR, 'ncbi_tree/names.dmp.gz')
NODES_DEF = join(TREEOFLIFE_DIR, 'ncbi_tree/nodes.dmp.gz')


def tokenize(filehandle):
    for line in filehandle:
        line = line.decode('utf-8')
        tkns = [tkn.strip() for tkn in line.strip().split(NCBI_DELIM)]
        yield tkns


class Command(BaseCommand):
    help = 'Populate the taxonomic tree with the NCBI tree'

    def handle(cls, *args, **kwargs):
        """Populate database tables with taxonomic info."""
        names_filename = environ.get(NAMES_ENV_VAR, NAMES_DEF)
        nodes_filename = environ.get(NODES_ENV_VAR, NODES_DEF)

        with gzip.open(names_filename) as names_file:
            for tkns in tokenize(names_file):
                TaxonName(taxon_id=tkns[0], name=tkns[1], name_type=tkns[2]).save()
        with gzip.open(nodes_filename) as nodes_file:
            for tkns in tokenize(nodes_file):
                TreeNode(node=tkns[0], parent=tkns[1], rank=tkns[2]).save()

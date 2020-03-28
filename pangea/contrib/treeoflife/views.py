import structlog

from django.db import connection
from django.utils.translation import gettext_lazy as _

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from pangea.core.utils import str2bool

from .models import TaxonName

logger = structlog.get_logger(__name__)


@api_view(['GET'])
def fuzzy_correct_taxa_names(request):
    """Reply with alternate taxa names."""
    logger.info(
        f'treeoflife__name_correction_query',
        query_params=request.query_params,
    )
    query = request.query_params.get('query', None)
    rank = request.query_params.get('rank', None)
    canon = request.query_params.get('canon', 'true').lower() != 'false'
    if query is None:
        logger.warn('treeoflife__name_correct_no_query_param')
        raise ValidationError(_('Must provide URL-encoded `query` query parameter.'))
    queries = query.split(',')
    results = {'canon': canon, 'rank': rank}
    for query in queries:
        result = {'query': query, 'names': []}
        nodes = {name.tree_node for name in TaxonName.objects.filter(name__icontains=query)}
        if canon:
            names = {node.canon_name for node in nodes if not rank or node.rank == rank}
        else:
            names = set()
            for node in nodes:
                if rank and node.rank != rank:
                    continue
                for name in node.all_names:
                    names.add(name)
        for name in names:
            result['names'].append({'name': name.name, 'taxon_id': name.taxon_id})
        results[query] = result

    return Response(results)


@api_view(['GET'])
def get_descendants(request):
    """Reply with descendant taxa."""
    logger.info(
        f'treeoflife__taxonomic_descendants',
        query_params=request.query_params,
    )
    queries = request.query_params.get('query', None).split(',')
    depth = int(request.query_params.get('depth', 1))
    annotate = request.query_params.get('annotate', 'false').lower() != 'false'

    def dfs(parent_node, parent, depth):
        if depth == 0:
            return
        for child in parent.children.all():
            child_node = {
                'name': child.canon_name.name,
                'taxon_id': child.taxon_id,
                'children': []
            }
            if annotate:
                child_node['annotation'] = child.annotation
            parent_node['children'].append(child_node)
            dfs(child_node, child, depth - 1)

    result = {'depth': depth}
    for query in queries:
        try:
            ancestor = TaxonName.objects.get(name__iexact=query).tree_node
        except ObjectDoesNotExist:
            raise ValidationError(_(f'Provided parameter {query} does not match any taxa.'))
        ancestor_node = {'name': ancestor.canon_name.name, 'taxon_id': ancestor.taxon_id, 'children': []}
        if annotate:
            ancestor_node['annotation'] = ancestor.annotation
        dfs(ancestor_node, ancestor, depth)
        result[query] = ancestor_node

    return Response(result)


@api_view(['GET'])
def annotate_taxa(request):
    """Reply with annotations for the taxa."""
    logger.info(
        f'treeoflife__annotate_taxa',
        query_params=request.query_params,
    )
    queries = request.query_params.get('query', None).split(',')
    result = {}
    for query in queries:
        try:
            taxon = TaxonName.objects.get(name__iexact=query).tree_node
        except ObjectDoesNotExist:
            raise ValidationError(_(f'Provided parameter {query} does not match any taxa.'))
        result[query] = taxon.annotation
    return Response(result)

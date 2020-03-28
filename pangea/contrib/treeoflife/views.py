import structlog

from django.db import connection
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from pangea.core.utils import str2bool

from .models import TaxonName

logger = structlog.get_logger(__name__)


@api_view(['GET'])
def fuzzy_correct_taxa_names(request):
    """Return samples with taxa results aggregated by city."""
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
    logger.info(
        f'treeoflife__responding_to_name_correction_query',
        query_params=request.query_params,
    )
    return Response(results)

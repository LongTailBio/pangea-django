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
    if query is None:
        logger.warn('treeoflife__name_correct_no_query_param')
        raise ValidationError(_('Must provide URL-encoded `query` query parameter.'))
    result = {'query': query, 'names': []}
    nodes = {name.tree_node for name in TaxonName.objects.filter(name__contains=query)}
    canon_names = {node.canon_name for node in nodes}
    for name in canon_names:
        result['names'].append({'name': name.name, 'taxon_id': name.taxon_id})
    logger.info(f'treeoflife__responding_to_name_correction_query', query=query)
    return Response(result)

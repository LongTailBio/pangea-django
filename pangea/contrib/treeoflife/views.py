import structlog

from django.db import connection
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from pangea.core.utils import str2bool

from .constants import METASUB_LIBRARY_UUID

logger = structlog.get_logger(__name__)


@api_view(['GET'])
def fuzzy_correct_taxa_names(request):
    """Return samples with taxa results aggregated by city."""
    query = request.query_params.get('query', None)
    if query is None:
        logger.warn('treeoflife__name_correct_no_query_param')
        raise ValidationError(_('Must provide URL-encoded `query` query parameter.'))
    canon = request.query_params.get('canon', True)
    result = {'query': query, 'names': [], 'canonical_names': canon}
    for obj in TreeName.objects.get(name__contains=query):
        if not canon or obj.name_type == 'scientific name':
            result['names'].append({'name': obj.name, 'taxon_id': obj.taxon_id})
    logger.info(f'treeoflife__responding_to_name_correction_query', query=query)
    return Response(result)

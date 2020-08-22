import structlog

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .search import omni_search

logger = structlog.get_logger(__name__)


@api_view(['GET'])
def get_omnisearch(request):
    """Return samples with taxa results that fuzzy match the query."""
    query = request.query_params.get('query', None)
    if query is None:
        logger.warn('omnisearch_search__no_query_param')
        raise ValidationError(_('Must provide URL-encoded `query` query parameter.'))

    results = omni_search(query)
    logger.info(f'omnisearch_search__responding_to_query', query=query)
    return Response({'results': results})

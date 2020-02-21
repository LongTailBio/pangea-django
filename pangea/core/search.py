
import structlog

from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .serializers import (
    SampleSerializer,
    SampleGroupSerializer,
    OrganizationSerializer,
)
from .models import (
    Sample,
    SampleGroup,
    Organization,
)

logger = structlog.get_logger(__name__)


@require_GET
def search_view(request):
    query = request.GET.get('q', '')
    try:
        sqs = SearchQuerySet().filter(content=AutoQuery(query))
    except:
        logger.error('search_failed', query=query)
        raise
    result = {
        'samples': [SampleSerializer(obj) for obj in sqs if isinstance(obj, Sample)],
        'sample_groups': [SampleGroupSerializer(obj) for obj in sqs if isinstance(obj, SampleGroup)],
        'organizations': [OrganizationSerializer(obj) for obj in sqs if isinstance(obj, Organization)],
    }
    logger.info(
        'conducted_search',
        query=query,
        n_sample_results=len(result['samples']),
        n_sample_group_results=len(result['sample_groups']),
        n_organization_results=len(result['organizations']),
    )
    return JsonResponse(result)

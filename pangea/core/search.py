
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

logger = structlog.get_logger(__name__)


@require_GET
def search_view(request):
    query = request.GET.get('q', '')
    try:
        sqs = SearchQuerySet().all()  # TODO: use the query
    except:
        logger.error('search_failed', query=query)
        raise

    def filter_serialize(model_name, serializer):
        return [serializer(res.object).data for res in sqs if res.model_name == model_name]

    result = {
        'samples': filter_serialize('sample', SampleSerializer),
        'sample_groups': filter_serialize('samplegroup', SampleGroupSerializer),
        'organizations': filter_serialize('organization', OrganizationSerializer),
    }
    logger.info(
        'conducted_search',
        query=query,
        n_sample_results=len(result['samples']),
        n_sample_group_results=len(result['sample_groups']),
        n_organization_results=len(result['organizations']),
    )
    return JsonResponse(result)

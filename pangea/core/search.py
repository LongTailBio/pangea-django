
import structlog

from haystack.query import SearchQuerySet
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import (
    SampleSerializer,
    SampleGroupSerializer,
    OrganizationSerializer,
)

logger = structlog.get_logger(__name__)


class SearchList(APIView):

    def get(self, request, format=None):
        query = request.GET.get('query', '')
        try:
            if query:
                sqs = SearchQuerySet().filter(name=query)
            else:
                sqs = SearchQuerySet().all()
        except:
            logger.exception('search_failed', query=query)
            raise

        def filter_serialize(model_name, serializer):
            return [serializer(res.object).data for res in sqs if res.model_name == model_name]

        result = {
            'query': query,
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
        return Response(result)

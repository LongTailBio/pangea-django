import structlog

from django.db import connection
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from pangea.core.utils import str2bool

logger = structlog.get_logger(__name__)


@api_view(['GET'])
def fuzzy_taxa_search(request):
    """Return samples with taxa results that fuzzy match the query."""
    metadata = str2bool(request.query_params.get('metadata', 'false'))
    query = request.query_params.get('query', None)
    if query is None:
        logger.warn('taxasearch__no_query_param')
        raise ValidationError(_('Must provide URL-encoded `query` query parameter.'))

    with connection.cursor() as cursor:
        query = f'%{query}%'
        cursor.execute(f'''
            -- Use text-based search to restrict the search space
            with clearcut as (
                select analysis_result_id, stored_data
                from core_sampleanalysisresultfield
                where name = 'relative_abundance'
                    and stored_data::text ilike %s
            ),
            -- Search on actual taxa results
            filtered_taxa as (
                select
                    clearcut.analysis_result_id,
                    taxa.*
                from
                    clearcut,
                    jsonb_each_text(clearcut.stored_data) as taxa
                where
                    taxa.key ilike %s
            )
            -- Pull in Sample records
            select
                filtered_taxa.key as taxa,
                json_agg((select x from (
                    select
                        filtered_taxa.value::float as relative_abundance,
                        core_sample.uuid as sample_uuid,
                        core_sample.name as sample_name,
                        core_sample.library_id as sample_library_uuid
                        {', core_sample.metadata as sample_metadata' if metadata else '' }
                    order by
                        core_sample.library_id
                ) as x)) as samples
            from
                core_sample
                join core_sampleanalysisresult
                    on core_sampleanalysisresult.sample_id = core_sample.uuid
                join filtered_taxa
                    on filtered_taxa.analysis_result_id = core_sampleanalysisresult.uuid
            group by
                filtered_taxa.key
            order by
                filtered_taxa.key
            ''', [query, query])

        results = {row[0]: row[1] for row in cursor.fetchall()}
        logger.info(f'taxasearch__responding_to_query', query=query)
        return Response({'results': results})

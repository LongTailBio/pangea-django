import structlog

from django.db import connection
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from pangea.core.utils import str2bool

from .constants import METASUB_LIBRARY_UUID

logger = structlog.get_logger(__name__)


def fuzzy_taxa_search(query):
    query = f'%{query}%'
    metasub_uuid = f'{METASUB_LIBRARY_UUID()}'
    with connection.cursor() as cursor:
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
                        core_sample.library_id as sample_library_uuid,
                        core_sample.metadata as sample_metadata
                    where
                        core_sample.library_id = %s
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
            ''', [query, query, metasub_uuid])

        results = {row[0]: row[1] for row in cursor.fetchall()}
    return results


@api_view(['GET'])
def fuzzy_taxa_search_samples(request):
    """Return samples with taxa results that fuzzy match the query."""
    query = request.query_params.get('query', None)
    if query is None:
        logger.warn('metasub_taxasearch__no_query_param')
        raise ValidationError(_('Must provide URL-encoded `query` query parameter.'))

    results = fuzzy_taxa_search(query)
    logger.info(f'metasub__responding_to_sample_query', query=query)
    return Response({'results': results})


@api_view(['GET'])
def fuzzy_taxa_search_cities(request):
    """Return samples with taxa results aggregated by city."""
    query = request.query_params.get('query', None)
    if query is None:
        logger.warn('metasub_taxasearch__no_query_param')
        raise ValidationError(_('Must provide URL-encoded `query` query parameter.'))

    results = fuzzy_taxa_search(query)
    city_results = {}
    for taxa_name, vals in results.items():
        city_results[taxa_name] = {}
        for val in vals:
            city = val['sample_metadata']['city']
            if city not in city_results[taxa_name]:
                city_results[taxa_name][city] = {
                    'mean_relative_abundance': [],
                    'city_name': city,
                }
                try:
                    city_results[taxa_name][city]['latitude'] = val['sample_metadata']['city_latitude']
                    city_results[taxa_name][city]['longitude'] = val['sample_metadata']['city_longitude']
                except KeyError:
                    pass
            city_results[taxa_name][city]['mean_relative_abundance'].append(val['relative_abundance'])
    for taxa_name, city in city_results.items():
        for city_name, vals in city.items():
            rels = vals['relative_abundance']
            vals['max_relative_abundance'] = max(rels)
            vals['mean_relative_abundance'] = sum(rels) / len(rels)

    logger.info(f'metasub__responding_to_city_query', query=query)
    return Response({'results': city_results})

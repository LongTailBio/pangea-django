from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from pangea.core.models import Sample


@api_view(['GET'])
def fuzzy_taxa_search(request):
    """Return samples with taxa results that fuzzy match the query."""
    query = request.query_params.get('query', None)
    if query is None:
        raise ValidationError(_('Must provide URL-encoded `query` query parameter.'))


    query = f'%{query}%'
    results = Sample.objects.raw('''
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
            core_sample.*,
            filtered_taxa.key as taxa,
            filtered_taxa.value::float as abundance
        from
            core_sample
            join core_sampleanalysisresult
                on core_sampleanalysisresult.sample_id = core_sample.uuid
            join filtered_taxa
                on filtered_taxa.analysis_result_id = core_sampleanalysisresult.uuid
        ''', [query, query])

    def search_result(sample):
        """Map query result to something serializable."""
        return {
            'uuid': sample.uuid,
            'name': sample.name,
            'taxa': sample.taxa,
            'abundance': sample.abundance,
        }

    return Response({'results': [search_result(result) for result in results]})

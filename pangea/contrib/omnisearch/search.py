
import structlog

from django.db import connection
from haystack.query import SearchQuerySet
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.exceptions import ValidationError
from pangea.contrib.treeoflife.models import TaxonName

from pangea.core.serializers import (
    SampleSerializer,
    SampleGroupSerializer,
    OrganizationSerializer,
)

logger = structlog.get_logger(__name__)


def is_dna(query):
    for char in query[:min(len(query, 100))]:
        if char not in 'ATCGUN':
            return False
    return True


def omni_search(query):
    out = {
        'keyword': keyword_search(query),
    }
    taxon_result = taxon_search(query)
    if taxon_result:
        taxon = taxon_result.canon_name
        out['taxon'] = {
            'canon_name': taxon,
            'annotation': taxon_result.annotation,
            'samples': fuzzy_taxa_search(taxon)[taxon]
        }
    if is_dna(query):
        dna_result = dna_search(query)
        out['nucleotide_sequence'] = dna_result
    return out


def taxon_search(taxon_query):
    try:
        taxon = TaxonName.objects.get(taxon_id=taxon_id).tree_node
    except ObjectDoesNotExist:
        try:
            taxon = TaxonName.objects.get(name__iexact=taxon_name).tree_node
        except ObjectDoesNotExist:
            return None
    return taxon


def dna_search(seq):
    return {}


def keyword_search(query):
    sqs = SearchQuerySet().filter(name=query)

    def filter_serialize(model_name, serializer):
        return [serializer(res.object).data for res in sqs if res.model_name == model_name]

    result = {
        'samples': filter_serialize('sample', SampleSerializer),
        'sample_groups': filter_serialize('samplegroup', SampleGroupSerializer),
        'organizations': filter_serialize('organization', OrganizationSerializer),
    }
    return result


def fuzzy_taxa_search(query):
    query = f'%{query}%'
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
                        core_sample.uuid as sample_uuid,
                        core_sample.name as sample_name,
                        core_sample.library_id as sample_library_uuid,
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
    return results


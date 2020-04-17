import structlog

from django.db import connection
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from pangea.core.utils import str2bool
from pangea.core.models import Sample, SampleAnalysisResultField
from pangea.contrib.treeoflife.taxa_tree import TaxaTree

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
                    'all_relative_abundances': [],
                    'city_name': city,
                }
                try:
                    city_results[taxa_name][city]['latitude'] = val['sample_metadata']['city_latitude']
                    city_results[taxa_name][city]['longitude'] = val['sample_metadata']['city_longitude']
                except KeyError:
                    pass
            city_results[taxa_name][city]['all_relative_abundances'].append(val['relative_abundance'])
    for taxa_name, city in city_results.items():
        for city_name, vals in city.items():
            rels = vals['all_relative_abundances']
            vals['max_relative_abundance'] = max(rels)
            vals['mean_relative_abundance'] = sum(rels) / len(rels)

    logger.info(f'metasub__responding_to_city_query', query=query)
    return Response({'results': city_results})


def normalize_surface(el):
    try:
        el = el.lower()
    except AttributeError:
        return el
    el = '_'.join(el.split())
    return {
        'ground': 'floor',
        'palm_left': 'human_hand',
        'vert_pole': 'pole',
        'palm_right': 'human_hand',
        'pedestrian_crossing_button': 'button',
        'wooden bench': 'seat',
        'gargabe_can': 'garbage',
        'horiz_pole': 'railing',
        'stairwell railing': 'railing',
        'bike kiosk': 'kiosk',
        'bench1': 'seat',
        'kiosk2': 'kiosk',
        'kiosk1': 'kiosk',
        'ticket_machine': 'kiosk',
        'escalator_handrail': 'railing',
        'bench2': 'seat',
        'lift_buttons': 'button',
        'overhead_handrail': 'railing',
        'poll': 'pole',
        'garbage_can': 'garbage',
        'bench': 'seat',
        'door_handle;door_handle': 'door_knob',
        'glass': 'window',
        'ceiling_rail': 'railing',
        'seat_rail': 'railing',
        'ticket_hall;ticket_machine': 'kiosk',
        'bench;platform': 'seat',
        'platform;bench': 'seat',
        'ticket_machine;ticket_hall': 'kiosk',
        'wooden_bench': 'seat',
        'stairwell_railing': 'railing',
        'trolley_handle': '',
        'turnstile_or_alternatives;turnstile_or_alternatives': 'turnstile',
        'ticket_kiosks;ticket_kiosks': 'kiosk',
        'ticket_machine;ticket_machine': 'kiosk',
        'station_eletronic_kiosk': 'kiosk',
        'station_railing': 'railing',
        'station_seat': 'seat',
        'center_seat': 'seat',
        'negative_control_(air)': '',
        'ceiling_rail;ceiling_rail': 'railing',
        'rail': 'railing',
        'seat_near_door': 'seat',
        'ticketing_machine;ticketing_machine_': 'kiosk',
        'jetway_1_seats_waiting_area': 'seat',
    }.get(el, el)


@api_view(['GET'])
def fuzzy_taxa_search_materials(request):
    """Return samples with taxa results aggregated by materials."""
    query = request.query_params.get('query', None)
    if query is None:
        logger.warn('metasub_taxasearch__no_query_param')
        raise ValidationError(_('Must provide URL-encoded `query` query parameter.'))

    results = fuzzy_taxa_search(query)
    material_results = {}
    for taxa_name, vals in results.items():
        material_results[taxa_name] = {}
        for val in vals:
            material = normalize_surface(val['sample_metadata'].get('surface', 'Other'))
            if material not in material_results[taxa_name]:
                material_results[taxa_name][material] = {
                    'all_relative_abundances': [],
                    'material_name': material,
                }
            material_results[taxa_name][material]['all_relative_abundances'] \
                .append(val['relative_abundance'])
    for taxa_name, material in material_results.items():
        for material_name, vals in material.items():
            rels = vals['all_relative_abundances']
            vals['max_relative_abundance'] = max(rels)
            vals['mean_relative_abundance'] = sum(rels) / len(rels)

    logger.info(f'metasub__responding_to_city_query', query=query)
    return Response({'results': material_results})


@api_view(['GET'])
def sample_taxonomy_sunburst(request, pk):
    """Reply with the taxonomy of a sample prepped for a Plotly sunburst plot."""
    min_abundance = float(request.query_params.get('min_abundance', 0.001))
    sample = Sample.objects \
        .filter(library_id=METASUB_LIBRARY_UUID()) \
        .get(uuid=pk)  # this clause ensures the sample is actually a MetaSUB sample
    taxa = SampleAnalysisResultField.objects \
        .filter(analysis_result__module_name='krakenuniq_taxonomy') \
        .filter(name='relative_abundance') \
        .get(analysis_result__sample__uuid=sample.uuid). \
        stored_data
    taxa = {taxon: val for taxon, val in taxa.items() if val >= min_abundance}
    taxa_list, parent_list = TaxaTree.get_taxon_parent_lists(taxa)
    abundances = [taxa.get(taxon, 0) for taxon in taxa_list]

    logger.info(f'metasub__responding_to_sample_taxonomy_sunburst_query', sample_uuid=pk)
    return Response({
        'taxa': taxa_list,
        'parents': parent_list,
        'abundances': abundances,
    })


@api_view(['GET'])
def all_taxa(request):
    """Reply with a list of all taxa names in MetaSUB."""
    taxa_relative_abundance = SampleAnalysisResultField.objects \
        .filter(analysis_result__module_name='krakenuniq_taxonomy') \
        .filter(name='relative_abundance')
    samples = Sample.objects.filter(library_id=METASUB_LIBRARY_UUID())
    taxa_list = set()
    for sample in samples:
        try:
            result_field = taxa_relative_abundance.get(analysis_result__sample__uuid=sample.uuid)
            for taxon in result_field.stored_data.keys():
                taxa_list.add(taxon.replace('_', ' '))
        except ObjectDoesNotExist:
            pass

    return Response({
        'taxa': list(taxa_list),
    })

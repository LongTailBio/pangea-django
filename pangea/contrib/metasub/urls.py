from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    fuzzy_taxa_search_samples,
    fuzzy_taxa_search_cities,
    fuzzy_taxa_search_materials,
    sample_taxonomy_sunburst,
    all_taxa,
    get_kobo_map_data
)


urlpatterns = {
    path('search_samples', fuzzy_taxa_search_samples, name="metasub-sample-taxa-search"),
    path('search_cities', fuzzy_taxa_search_cities, name="metasub-city-taxa-search"),
    path('search_materials', fuzzy_taxa_search_materials, name="metasub-materials-taxa-search"),
    path('all_taxa', all_taxa, name="metasub-all-taxa"),
    path('sample_sunburst/<uuid:pk>', sample_taxonomy_sunburst, name='metasub-sample-sunburst'),
    path('kobo_map', get_kobo_map_data, name='get-kobo-map-data')
}


urlpatterns = format_suffix_patterns(urlpatterns)

from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    fuzzy_taxa_search_samples,
    fuzzy_taxa_search_cities,
    sample_taxonomy_sunburst,
    all_taxa,
)


urlpatterns = {
    path('search_samples', fuzzy_taxa_search_samples, name="metasub-sample-taxa-search"),
    path('search_cities', fuzzy_taxa_search_cities, name="metasub-city-taxa-search"),
    path('all_taxa', all_taxa, name="metasub-all-taxa"),
    path('sample_sunburst/<uuid:pk>', sample_taxonomy_sunburst, name='metasub-sample-sunburst'),
}


urlpatterns = format_suffix_patterns(urlpatterns)

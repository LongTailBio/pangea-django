from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    fuzzy_taxa_search_samples,
    fuzzy_taxa_search_cities,
)


urlpatterns = {
    path('search_samples', fuzzy_taxa_search_samples, name="metasub-sample-taxa-search"),
    path('search_cities', fuzzy_taxa_search_cities, name="metasub-city-taxa-search"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

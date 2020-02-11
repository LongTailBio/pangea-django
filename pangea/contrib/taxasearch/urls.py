from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import fuzzy_taxa_search


urlpatterns = {
    path('search', fuzzy_taxa_search, name="taxa-search"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

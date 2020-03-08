from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    fuzzy_correct_taxa_names,
)


urlpatterns = {
    path('correct_names', fuzzy_correct_taxa_names, name="treeoflife-correct-taxa-names"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

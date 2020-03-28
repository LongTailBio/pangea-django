from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    fuzzy_correct_taxa_names,
    get_descendants,
)


urlpatterns = {
    path('correct_names', fuzzy_correct_taxa_names, name="treeoflife-correct-taxa-names"),
    path('get_descendants', get_descendants, name="treeoflife-get-descendants"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

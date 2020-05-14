from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    get_omnisearch
)


urlpatterns = {
    path('search', get_omnisearch, name="omnisearch-search"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

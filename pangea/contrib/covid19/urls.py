from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import Covid19ListCreateView


urlpatterns = {
    path('', Covid19ListCreateView.as_view(), name="covid19-list"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

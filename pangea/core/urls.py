from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    OrganizationCreateView, OrganizationDetailsView,
    SampleGroupCreateView, SampleGroupDetailsView,
    SampleCreateView, SampleDetailsView,
    SampleAnalysisResultDetailsView,
    SampleGroupAnalysisResultDetailsView,
)


# TODO: add routes for remaining models
urlpatterns = {
    path('organizations', OrganizationCreateView.as_view(), name="create"),
    path('organizations/<uuid:pk>', OrganizationDetailsView.as_view(), name="details"),
    path('sample_groups', SampleGroupCreateView.as_view(), name="create"),
    path('sample_groups/<uuid:pk>', SampleGroupDetailsView.as_view(), name="details"),
    path('samples', SampleCreateView.as_view(), name="create"),
    path('samples/<uuid:pk>', SampleDetailsView.as_view(), name="details"),
    path('sample_ars', SampleAnalysisResultDetailsView.as_view(), name="details"),
    path('sample_group_ars', SampleGroupAnalysisResultDetailsView.as_view(), name="create"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

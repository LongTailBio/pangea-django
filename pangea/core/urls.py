from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    OrganizationCreateView, OrganizationDetailsView,
    SampleGroupCreateView, SampleGroupDetailsView,
    SampleCreateView, SampleDetailsView,
    SampleAnalysisResultCreateView, SampleAnalysisResultDetailsView,
    SampleGroupAnalysisResultCreateView, SampleGroupAnalysisResultDetailsView,
)


urlpatterns = {
    path('organizations', OrganizationCreateView.as_view(), name="create"),
    path('organizations/<uuid:pk>', OrganizationDetailsView.as_view(), name="details"),
    path('sample_groups', SampleGroupCreateView.as_view(), name="create"),
    path('sample_groups/<uuid:pk>', SampleGroupDetailsView.as_view(), name="details"),
    path('samples', SampleCreateView.as_view(), name="create"),
    path('samples/<uuid:pk>', SampleDetailsView.as_view(), name="details"),
    path('sample_ars', SampleAnalysisResultCreateView.as_view(), name="create"),
    path('sample_ars/<uuid:pk>', SampleAnalysisResultDetailsView.as_view(), name="details"),
    path('sample_group_ars', SampleGroupAnalysisResultCreateView.as_view(), name="create"),
    path('sample_group_ars/<uuid:pk>', SampleGroupAnalysisResultDetailsView.as_view(), name="details"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

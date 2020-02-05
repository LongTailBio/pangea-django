from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import OrganizationCreateView, OrganizationDetailsView


# TODO: add routes for remaining models
urlpatterns = {
    path('organizations', OrganizationCreateView.as_view(), name="create"),
    path('organizations/<uuid:pk>', OrganizationDetailsView.as_view(), name="details"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

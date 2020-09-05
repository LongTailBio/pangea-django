from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    TagCreateView, TagDetailsView,
    TagTagsView, TagSampleGroupsView, TagSamplesView,
)


urlpatterns = {
    path('', TagCreateView.as_view(), name="tag-create"),
    path('<uuid:pk>', TagDetailsView.as_view(), name="tag-details"),
    path('<uuid:tag_pk>/tags', TagTagsView.as_view(), name="tag-tags"),
    path('<uuid:tag_pk>/sample_groups', TagSampleGroupsView.as_view(), name="tag-sample-groups"),
    path('<uuid:tag_pk>/samples', TagSamplesView.as_view(), name="tag-samples"),
}


urlpatterns = format_suffix_patterns(urlpatterns)

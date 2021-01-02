from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    TagCreateView, TagDetailsView, TagNameDetailsView,
    TagTagsView, TagSampleGroupsView, TagSamplesView,
    get_random_samples_in_tag,
)


urlpatterns = {
    path('', TagCreateView.as_view(), name="tag-create"),
    path('<uuid:pk>', TagDetailsView.as_view(), name="tag-details"),
    path('name/<name>', TagNameDetailsView.as_view(), name="tag-name-details"),
    path('<uuid:tag_pk>/tags', TagTagsView.as_view(), name="tag-tags"),
    path('<uuid:tag_pk>/sample_groups', TagSampleGroupsView.as_view(), name="tag-sample-groups"),
    path('<uuid:tag_pk>/samples', TagSamplesView.as_view(), name="tag-samples"),
    path('<uuid:tag_pk>/random_samples', get_random_samples_in_tag, name="tag-random-samples"),

}


urlpatterns = format_suffix_patterns(urlpatterns)

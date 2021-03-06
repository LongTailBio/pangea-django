from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    OrganizationCreateView, OrganizationDetailsView,
    OrganizationUsersView,
    S3ApiKeyCreateView, S3ApiKeyDetailsView,
    S3BucketCreateView, S3BucketDetailsView,
    SampleGroupCreateView, SampleGroupDetailsView,
    SampleGroupSamplesView, get_sample_group_manifest,
    ProjectCreateView, ProjectDetailsView, ProjectSampleGroupsView,
    get_sample_ar_counts_in_group, get_sample_metadata_in_group,
    get_sample_data_in_group,
    SampleCreateView, SampleDetailsView,
    get_sample_manifest,
    SampleAnalysisResultCreateView, SampleAnalysisResultDetailsView,
    SampleGroupAnalysisResultCreateView, SampleGroupAnalysisResultDetailsView,
    SampleAnalysisResultFieldCreateView, SampleAnalysisResultFieldDetailsView,
    post_sample_ar_upload_url, post_sample_ar_complete_multipart_upload_url,
    post_sample_group_ar_upload_url, post_sample_group_ar_complete_multipart_upload_url,
    SampleGroupAnalysisResultFieldCreateView, SampleGroupAnalysisResultFieldDetailsView,
)
from .search import SearchList


urlpatterns = {
    path('organizations', OrganizationCreateView.as_view(), name="organization-create"),
    path('organizations/<uuid:pk>', OrganizationDetailsView.as_view(), name="organization-details"),
    path('organizations/<uuid:organization_pk>/users', OrganizationUsersView.as_view(), name="organization-users"),

    path('s3_api_keys', S3ApiKeyCreateView.as_view(), name='s3apikey-create'),
    path('s3_buckets/<uuid:pk>', S3ApiKeyDetailsView.as_view(), name='s3apikey-details'),
    path('s3_api_keys/<uuid:pk>', S3BucketDetailsView.as_view(), name='s3bucket-details'),
    path('s3_buckets', S3BucketCreateView.as_view(), name='s3bucket-create'),

    path('projects', ProjectCreateView.as_view(), name="project-create"),
    path('projects/<uuid:pk>', ProjectDetailsView.as_view(), name="project-details"),
    path('projects/<uuid:project_pk>/sample_groups', ProjectSampleGroupsView.as_view(), name="project-sample-groups"),


    path('sample_groups', SampleGroupCreateView.as_view(), name="sample-group-create"),
    path('sample_groups/<uuid:pk>', SampleGroupDetailsView.as_view(), name="sample-group-details"),
    path('sample_groups/<uuid:pk>/manifest', get_sample_group_manifest, name="sample-group-manifest"),
    path('sample_groups/<uuid:pk>/metadata', get_sample_metadata_in_group, name="sample-group-metadata"),
    path('sample_groups/<uuid:pk>/downloads/<str:module_name>', get_sample_data_in_group, name="sample-group-download"),
    path('sample_groups/<uuid:pk>/module_counts', get_sample_ar_counts_in_group, name="sample-group-module-counts"),
    path('sample_groups/<uuid:group_pk>/samples', SampleGroupSamplesView.as_view(), name="sample-group-samples"),

    path('samples', SampleCreateView.as_view(), name="sample-create"),
    path('samples/<uuid:pk>', SampleDetailsView.as_view(), name="sample-details"),
    path('samples/<uuid:pk>/manifest', get_sample_manifest, name="sample-manifest"),

    path('sample_ars', SampleAnalysisResultCreateView.as_view(), name="sample-ars-create"),
    path('sample_ars/<uuid:pk>', SampleAnalysisResultDetailsView.as_view(), name="sample-ars-details"),

    path('sample_group_ars', SampleGroupAnalysisResultCreateView.as_view(), name="sample-group-ars-create"),
    path('sample_group_ars/<uuid:pk>', SampleGroupAnalysisResultDetailsView.as_view(), name="sample-group-ars-details"),

    path('sample_ar_fields', SampleAnalysisResultFieldCreateView.as_view(), name="sample-ar-fields-create"),
    path('sample_ar_fields/<uuid:pk>', SampleAnalysisResultFieldDetailsView.as_view(), name="sample-ar-fields-details"),
    path('sample_ar_fields/<uuid:pk>/upload_s3', post_sample_ar_upload_url, name="sample-ar-fields-get-upload-url"),
    path('sample_ar_fields/<uuid:pk>/complete_upload_s3', post_sample_ar_complete_multipart_upload_url, name="sample-ar-fields-get-upload-complete-url"),

    path('sample_group_ar_fields/<uuid:pk>/upload_s3', post_sample_group_ar_upload_url, name="sample-group-ar-fields-get-upload-url"),
    path('sample_group_ar_fields/<uuid:pk>/complete_upload_s3', post_sample_group_ar_complete_multipart_upload_url, name="sample-group-ar-fields-get-upload-complete-url"),
    path('sample_group_ar_fields', SampleGroupAnalysisResultFieldCreateView.as_view(), name="sample-group-ar-fields-create"),
    path('sample_group_ar_fields/<uuid:pk>', SampleGroupAnalysisResultFieldDetailsView.as_view(), name="sample-group-ar-fields-details"),

    path('search', SearchList.as_view(), name="search"),
}

urlpatterns = format_suffix_patterns(urlpatterns)

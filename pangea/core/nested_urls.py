'''
Additional URLs that support nested access and access by name.
/{org_pk}/
/{org_pk}/sample_groups/
/{org_pk}/sample_groups/{grp_pk}/
/{org_pk}/sample_groups/{grp_pk}/analysis_results
/{org_pk}/sample_groups/{grp_pk}/analysis_results/{ar_pk}
/{org_pk}/sample_groups/{grp_pk}/analysis_results/{ar_pk}/fields
/{org_pk}/sample_groups/{grp_pk}/analysis_results/{ar_pk}/fields/{field_pk}
/{org_pk}/sample_groups/{grp_pk}/samples/
/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/
/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results
/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results/{ar_pk}
/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results/{ar_pk}/fields
/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results/{ar_pk}/fields/{field_pk}
'''

from django.urls import path
from django.db.models.functions import Lower
from uuid import UUID
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    OrganizationDetailsView,
    SampleGroupCreateView, SampleGroupDetailsView,
    SampleCreateView, SampleDetailsView,
    SampleAnalysisResultCreateView, SampleAnalysisResultDetailsView,
    SampleGroupAnalysisResultCreateView, SampleGroupAnalysisResultDetailsView,
    SampleAnalysisResultFieldCreateView, SampleAnalysisResultFieldDetailsView,
    SampleGroupAnalysisResultFieldCreateView, SampleGroupAnalysisResultFieldDetailsView,
)
from .models import (
    Organization,
    SampleGroup,
    Sample,
    SampleAnalysisResult,
    SampleGroupAnalysisResult,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
)


def is_uuid(el):
    """Return true if el is an UUID."""
    try:
        UUID(el)
        return True
    except ValueError:
        return False


def to_uuid(**kwargs):
    """Return a UUID and a field name for the lowest parent level in the URL."""
    # Keys are:
    # - named path parameter
    # - name of the model's foreign key to its parent
    # - model
    # - name of parent id parameter in create payload
    keys = [('grp_pk', 'organization', SampleGroup, 'sample_group')]
    # Identify which routing branch was taken based on presence of named path params
    if 'sample_pk' in kwargs:
        keys += [
            ('sample_pk', 'library', Sample, 'sample'),
            ('ar_pk', 'sample', SampleAnalysisResult, 'analysis_result'),
            ('field_pk', 'analysis_result', SampleAnalysisResultField, None),
        ]
    else:
        keys += [
            ('ar_pk', 'sample_group', SampleGroupAnalysisResult, 'analysis_result'),
            ('field_pk', 'analysis_result', SampleGroupAnalysisResultField, None),
        ]
    org_key = kwargs['org_pk']
    parent_field_name = 'organization'
    if is_uuid(org_key):
        parent = Organization.objects.get(pk=org_key)
    else:
        parent = Organization.objects.get(name__iexact=org_key)

    # Traverse down through whichever path segments present in the request
    for uuid_key, parent_key_name, model, field_name in keys:
        if uuid_key not in kwargs:
            break
        filter_field = 'pk' if is_uuid(kwargs[uuid_key]) else 'name__iexact'
        if filter_field != 'pk' and model in [SampleAnalysisResult, SampleGroupAnalysisResult]:
            filter_field = 'module_name__iexact'
        if filter_field != 'pk' and model in [SampleAnalysisResultField, SampleGroupAnalysisResultField]:
            filter_field = 'field_name__iexact'
        parent = model.objects.get(**{
            parent_key_name: parent.uuid,
            filter_field: kwargs[uuid_key],
        })
        parent_field_name = field_name
    return parent.uuid, parent_field_name


def nested_path(url, base_view, *out_args, **out_kwargs):
    """Return a path with an intercepted view function."""
    create = out_kwargs.pop('create', False)

    def my_request(request, *args, **kwargs):
        """Return the result of the base view function with a modified result."""
        uuid_kwargs = {}
        for key in ['org_pk', 'grp_pk', 'sample_pk', 'ar_pk', 'field_pk']:
            if key in kwargs:
                uuid_kwargs[key] = kwargs.pop(key)
        uuid, field_name = to_uuid(**uuid_kwargs)
        if create:
            post = request.POST.copy()
            post[field_name] = uuid
            request.POST = post
        else:
            kwargs['pk'] = uuid
        return base_view(request, *args, **kwargs)

    return path(url, my_request, *out_args, **out_kwargs)


urlpatterns = {
    nested_path(
        '<org_pk>/',
        OrganizationDetailsView.as_view(),
        name="nested-organization-detail"
    ),
    nested_path(
        '<org_pk>/sample_groups/',
        SampleGroupCreateView.as_view(),
        create=True,
        name="nested-sample-group-create"
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/',
        SampleGroupDetailsView.as_view(),
        name="nested-sample-group-detail"
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/analysis_results',
        SampleGroupAnalysisResultCreateView.as_view(),
        create=True,
        name='nested-sample-group-ar-create',
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/analysis_results/<ar_pk>',
        SampleGroupAnalysisResultDetailsView.as_view(),
        name='nested-sample-group-ar-details',
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/analysis_results/<ar_pk>/fields',
        SampleGroupAnalysisResultFieldCreateView.as_view(),
        create=True,
        name='nested-sample-group-ar-field-create',
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/analysis_results/<ar_pk>/fields/<field_pk>',
        SampleGroupAnalysisResultFieldDetailsView.as_view(),
        name='nested-sample-group-ar-field-details',
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/samples/',
        SampleCreateView.as_view(),
        create=True,
        name='nested-sample-create',
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/samples/<sample_pk>/',
        SampleDetailsView.as_view(),
        name='nested-sample-details',
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/samples/<sample_pk>/analysis_results',
        SampleAnalysisResultCreateView.as_view(),
        create=True,
        name='nested-sample-ar-create',
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/samples/<sample_pk>/analysis_results/<ar_pk>',
        SampleAnalysisResultDetailsView.as_view(),
        name='nested-sample-ar-details',
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/samples/<sample_pk>/analysis_results/<ar_pk>/fields',
        SampleAnalysisResultFieldCreateView.as_view(),
        create=True,
        name='nested-sample-ar-field-create',
    ),
    nested_path(
        '<org_pk>/sample_groups/<grp_pk>/samples/<sample_pk>/analysis_results/<ar_pk>/fields/<field_pk>',
        SampleAnalysisResultFieldDetailsView.as_view(),
        name='nested-sample-ar-field-details',
    )
}
urlpatterns = format_suffix_patterns(urlpatterns)

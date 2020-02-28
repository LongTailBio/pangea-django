
from django.urls import path, include
from uuid import UUID
from django.conf.urls import url
from rest_framework_nested import routers
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    OrganizationCreateView, OrganizationDetailsView,
    OrganizationUsersView,
    SampleGroupCreateView, SampleGroupDetailsView,
    SampleGroupSamplesView,
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

'''
/organizations/
/organizations/{org_pk}/
/organizations/{org_pk}/sample_groups/
/organizations/{org_pk}/sample_groups/{grp_pk}/
/organizations/{org_pk}/sample_groups/{grp_pk}/analysis_results
/organizations/{org_pk}/sample_groups/{grp_pk}/analysis_results/{ar_pk}
/organizations/{org_pk}/sample_groups/{grp_pk}/analysis_results/{ar_pk}/fields
/organizations/{org_pk}/sample_groups/{grp_pk}/analysis_results/{ar_pk}/fields/{field_pk}
/organizations/{org_pk}/sample_groups/{grp_pk}/samples/
/organizations/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/
/organizations/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results
/organizations/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results/{ar_pk}
/organizations/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results/{ar_pk}/fields
/organizations/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results/{ar_pk}/fields/{field_pk}
'''

def is_uuid(el):
    return isinstance(el, UUID)


def to_uuid(**kwargs):
    keys = [('grp_pk', 'organization', SampleGroup, 'sample_group')]
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
        parent = Organization.objects.get(name=org_key)
    for uuid_key, parent_key_name, model, field_name in keys:
        if uuid_key not in kwargs:
            break
        parent = model.objects.filter(**{
            parent_key_name: parent.uuid,
            'pk' if is_uuid(kwargs[uuid_key]) else 'name': kwargs[uuid_key],
        })[0]
        parent_field_name = field_name
    return parent.uuid, parent_field_name


def mypath(url, base_view, *out_args, **out_kwargs):

    create = out_kwargs.pop('create', False)

    def my_request(request, *args, **kwargs):
        uuid_kwargs = {}
        for key in ['org_pk', 'grp_pk', 'sample_pk', 'ar_pk', 'field_pk']:
            if key in kwargs:
                uuid_kwargs[key] = kwargs.pop(key)
        uuid, field_name = to_uuid(**uuid_kwargs)
        if create:
            kwargs['pk'] = uuid
        else:
            request.data[field_name] = uuid
        return base_view(request, *args, **kwargs)

    return path(url, my_request, *out_args, **out_kwargs)


urlpatterns = {
    mypath('<uuid:org_pk>/', OrganizationDetailsView.as_view(), name="nested-organization-detail"),
    mypath(
        '<uuid:org_pk>/sample_groups/',
        SampleGroupCreateView.as_view(),
        create=True,
        name="nested-sample-group-create"
    )
    # path('/{org_pk}/sample_groups/{grp_pk}/', )
    # path('/{org_pk}/sample_groups/{grp_pk}/analysis_results', )
    # path('/{org_pk}/sample_groups/{grp_pk}/analysis_results/{ar_pk}', )
    # path('/{org_pk}/sample_groups/{grp_pk}/analysis_results/{ar_pk}/fields', )
    # path('/{org_pk}/sample_groups/{grp_pk}/analysis_results/{ar_pk}/fields/{field_pk}', )
    # path('/{org_pk}/sample_groups/{grp_pk}/samples/', )
    # path('/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/', )
    # path('/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results', )
    # path('/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results/{ar_pk}', )
    # path('/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results/{ar_pk}/fields', )
    # path('/{org_pk}/sample_groups/{grp_pk}/samples/{sample_pk}/analysis_results/{ar_pk}/fields/{field_pk}', )
}
urlpatterns = format_suffix_patterns(urlpatterns)

'''
router = routers.DefaultRouter()
router.register(r'organizations', OrganizationCreateView)
router.register('organizations/<uuid:pk>', OrganizationDetailsView.as_view(), basename='foo')

org_router = routers.NestedDefaultRouter(router, r'organizations', lookup='org')
org_router.register('sample_groups', SampleGroupCreateView)
org_router.register('sample_groups/<uuid:pk>', SampleGroupDetailsView)

groups_router = routers.NestedDefaultRouter(org_router, r'sample_groups', lookup='grp')
groups_router.register('analysis_results', SampleGroupAnalysisResultCreateView, base_name='group_analysis_results')
groups_router.register('analysis_results/<uuid:pk>', SampleGroupAnalysisResultDetailsView, base_name='group_analysis_results')
groups_router.register('samples', SampleCreateView, base_name='samples')
groups_router.register('samples/<uuid:pk>', SampleDetailsView, base_name='samples')

groups_ar_router = routers.NestedDefaultRouter(groups_router, r'analysis_results', lookup='ar')
groups_ar_router.register('field', SampleGroupAnalysisResultFieldCreateView, base_name='group_analysis_result_fields')
groups_ar_router.register('field/<uuid:pk>', SampleGroupAnalysisResultFieldDetailsView, base_name='group_analysis_result_fields')

samples_router = routers.NestedDefaultRouter(groups_router, r'samples', lookup='sample')
sample_router.register('analysis_results', SampleAnalysisResultCreateView, base_name='sample_analysis_results')
sample_router.register('analysis_results/<uuid:pk>', SampleAnalysisResultDetailsView, base_name='sample_analysis_results')

samples_ar_router = routers.NestedDefaultRouter(samples_router, r'analysis_results', lookup='ar')
samples_ar_router.register('field', SampleAnalysisResultFieldCreateView, base_name='sample_analysis_result_fields')
samples_ar_router.register('field/<uuid:pk>', SampleAnalysisResultFieldDetailsView, base_name='sample_analysis_result_fields')

urlpatterns = [
    '',
    url(r'^', include(router.urls)),
    # url(r'^', include(org_router.urls)),
    # url(r'^', include(groups_router.urls)),
    # url(r'^', include(groups_ar_router.urls)),
    # url(r'^', include(sample_router.urls)),
    # url(r'^', include(sample_ar_router.urls)),
]
'''

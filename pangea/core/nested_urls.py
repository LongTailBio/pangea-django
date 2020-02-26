
from rest_framework_nested import routers

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

router = routers.DefaultRouter()
router.register(r'organizations', OrganizationCreateView, base_name='organizations')
router.register('organizations/<uuid:pk>', OrganizationDetailsView, base_name='organizations')

org_router = routers.NestedSimpleRouter(router, r'organizations', lookup='org')
org_router.register('sample_groups', SampleGroupCreateView, base_name='sample_groups')
org_router.register('sample_groups/<uuid:pk>', SampleGroupDetailsView, base_name='sample_groups')

groups_router = routers.NestedSimpleRouter(org_router, r'sample_groups', lookup='grp')
groups_router.register('analysis_results', SampleGroupAnalysisResultCreateView, base_name='group_analysis_results')
groups_router.register('analysis_results/<uuid:pk>', SampleGroupAnalysisResultDetailsView, base_name='group_analysis_results')
groups_router.register('samples', SampleCreateView, base_name='samples')
groups_router.register('samples/<uuid:pk>', SampleDetailsView, base_name='samples')

groups_ar_router = routers.NestedSimpleRouter(groups_router, r'analysis_results', lookup='ar')
groups_ar_router.register('field', SampleGroupAnalysisResultFieldCreateView, base_name='group_analysis_result_fields')
groups_ar_router.register('field/<uuid:pk>', SampleGroupAnalysisResultFieldDetailsView, base_name='group_analysis_result_fields')

samples_router = routers.NestedSimpleRouter(groups_router, r'samples', lookup='sample')
sample_router.register('analysis_results', SampleAnalysisResultCreateView, base_name='sample_analysis_results')
sample_router.register('analysis_results/<uuid:pk>', SampleAnalysisResultDetailsView, base_name='sample_analysis_results')

samples_ar_router = routers.NestedSimpleRouter(samples_router, r'analysis_results', lookup='ar')
samples_ar_router.register('field', SampleAnalysisResultFieldCreateView, base_name='sample_analysis_result_fields')
samples_ar_router.register('field/<uuid:pk>', SampleAnalysisResultFieldDetailsView, base_name='sample_analysis_result_fields')


urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    url(r'^', include(org_router.urls)),
    url(r'^', include(groups_router.urls)),
    url(r'^', include(groups_ar_router.urls)),
    url(r'^', include(sample_router.urls)),
    url(r'^', include(sample_ar_router.urls)),
)

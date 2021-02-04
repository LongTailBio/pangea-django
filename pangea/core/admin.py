from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _


from .forms import PangeaUserCreationForm, PangeaUserChangeForm
from .models import (
    PangeaUser,
    Organization,
    Project,
    S3ApiKey,
    S3Bucket,
    SampleGroup,
    SampleLibrary,
    Sample,
    SampleGroupAnalysisResult,
    SampleGroupAnalysisResultField,
    SampleAnalysisResult,
    SampleAnalysisResultField,
    VersionedMetadata,
    Pipeline,
    PipelineModule,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'members',)

    def members(self, obj):
        return obj.users.count()


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization',)
    list_filter = (
        ('organization', admin.RelatedOnlyFieldListFilter),
    )


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(PipelineModule)
class PipelineModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'pipeline',)
    list_filter = (
        ('pipeline', admin.RelatedOnlyFieldListFilter),
    )


@admin.register(S3Bucket)
class S3BucketAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'endpoint_url',)
    list_filter = (
        ('organization', admin.RelatedOnlyFieldListFilter),
    )

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'organization__uuid__exact',
        ]

    def organization_name(self, obj):
        return obj.organization.name


@admin.register(S3ApiKey)
class S3ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('public_key', 'bucket_name',)

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'bucket__uuid__exact',
        ]

    def bucket_name(self, obj):
        return obj.bucket.name

    def organization_name(self, obj):
        return obj.bucket.organization.name


@admin.register(SampleGroup)
class SampleGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_name',)
    list_filter = (
        ('organization', admin.RelatedOnlyFieldListFilter),
    )

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'organization__uuid__exact',
        ]

    def organization_name(self, obj):
        return obj.organization.name


@admin.register(SampleLibrary)
class SampleLibraryAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_name',)
    list_filter = (
        ('group__organization', admin.RelatedOnlyFieldListFilter),
    )

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'group__organization__uuid__exact',
        ]

    def organization_name(self, obj):
        return obj.group.organization.name

    def name(self, obj):
        return f'{obj.group.name} (library)'


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('name', 'library_name','member_of_groups',)
    list_filter = (
        ('library__group__organization', admin.RelatedOnlyFieldListFilter),
        ('library', admin.RelatedOnlyFieldListFilter),
    )

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'library__group__organization__uuid__exact',
            'library__group__exact',
        ]

    def library_name(self, obj):
        return obj.library.group.name

    def member_of_groups(self, obj):
        return ", ".join([group.name for group in obj.sample_groups.only('name')])


@admin.register(VersionedMetadata)
class VersionedMetadataAdmin(admin.ModelAdmin):
    list_display = ('sample', 'updated_at', 'created_at')
    list_filter = (
        ('sample__library__group__organization', admin.RelatedOnlyFieldListFilter),
        ('sample__library', admin.RelatedOnlyFieldListFilter),
    )

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'sample__library__group__organization__uuid__exact',
            'sample__library__group__exact',
        ]


@admin.register(SampleAnalysisResult)
class SampleAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('sample_name', 'module_name',)
    list_filter = (
        ('sample__library__group__organization', admin.RelatedOnlyFieldListFilter),
        ('sample__library__group', admin.RelatedOnlyFieldListFilter),
        'module_name',
        ('sample', admin.RelatedOnlyFieldListFilter),
    )

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'sample__library__group__organization__uuid__exact',
            'sample__library__group__uuid__exact',
            'sample__uuid__exact',
            'module_name',
        ]

    def sample_name(self, obj):
        return obj.sample.name


class FieldNameListFilter(admin.AllValuesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = _('field name')


@admin.register(SampleAnalysisResultField)
class SampleAnalysisResultFieldAdmin(admin.ModelAdmin):
    list_display = ('sample_name', 'module_name', 'field_name')
    list_filter = (
        ('analysis_result__sample__library__group__organization', admin.RelatedOnlyFieldListFilter),
        ('analysis_result__sample__library__group', admin.RelatedOnlyFieldListFilter),
        'analysis_result__module_name',
        ('name', FieldNameListFilter),
        ('analysis_result__sample', admin.RelatedOnlyFieldListFilter),
    )

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'analysis_result__sample__library__group__organization__uuid__exact',
            'analysis_result__sample__library__group__uuid__exact',
            'analysis_result__sample__uuid__exact',
            'analysis_result__module_name',
            'name',
        ]

    def sample_name(self, obj):
        return obj.analysis_result.sample.name

    def module_name(self, obj):
        return obj.analysis_result.module_name

    def field_name(self, obj):
        return obj.name


@admin.register(SampleGroupAnalysisResult)
class SampleGroupAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('sample_group_name', 'module_name',)
    list_filter = (
        ('sample_group__organization', admin.RelatedOnlyFieldListFilter),
        ('sample_group', admin.RelatedOnlyFieldListFilter),
        'module_name',
    )

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'sample_group__organization__uuid__exact',
            'sample_group__uuid__exact',
            'module_name',
        ]

    def sample_group_name(self, obj):
        return obj.sample_group.name


@admin.register(SampleGroupAnalysisResultField)
class SampleGroupAnalysisResultFieldAdmin(admin.ModelAdmin):
    list_display = ('sample_group_name', 'module_name', 'field_name')
    list_filter = (
        ('analysis_result__sample_group__organization', admin.RelatedOnlyFieldListFilter),
        ('analysis_result__sample_group', admin.RelatedOnlyFieldListFilter),
        'analysis_result__module_name',
        ('name', FieldNameListFilter),
    )

    def lookup_allowed(self, lookup, value):
        return lookup in [
            'analysis_result__sample_group__organization__uuid__exact',
            'analysis_result__sample_group__uuid__exact',
            'analysis_result__module_name',
            'name',
        ]

    def sample_group_name(self, obj):
        return obj.analysis_result.sample_group.name

    def module_name(self, obj):
        return obj.analysis_result.module_name

    def field_name(self, obj):
        return obj.name


class PangeaUserAdmin(UserAdmin):
    add_form = PangeaUserCreationForm
    form = PangeaUserChangeForm
    model = PangeaUser
    list_display = ('email', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)


admin.site.register(PangeaUser, PangeaUserAdmin)

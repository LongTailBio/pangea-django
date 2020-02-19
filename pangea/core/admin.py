from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


from .forms import PangeaUserCreationForm, PangeaUserChangeForm
from .models import (
    PangeaUser,
    Organization,
    SampleGroup,
    SampleLibrary,
    Sample,
    SampleGroupAnalysisResult,
    SampleGroupAnalysisResultField,
    SampleAnalysisResult,
    SampleAnalysisResultField
)

@admin.register(Organization, SampleGroup, SampleLibrary, Sample, SampleGroupAnalysisResult,
                SampleGroupAnalysisResultField, SampleAnalysisResult, SampleAnalysisResultField)
class PangeaCoreAdmin(admin.ModelAdmin):
    pass


class PangeaUserAdmin(UserAdmin):
    add_form = PangeaUserCreationForm
    form = PangeaUserChangeForm
    model = PangeaUser
    filter_horizontal = ('Organization', 'SampleGroup')
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

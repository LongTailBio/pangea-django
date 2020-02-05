from django.contrib import admin

from .models import (
    Organization,
    SampleGroup,
    Sample,
    SampleGroupAnalysisResult,
    SampleGroupAnalysisResultField,
    SampleAnalysisResult,
    SampleAnalysisResultField
)

@admin.register(Organization, SampleGroup, Sample, SampleGroupAnalysisResult,
                SampleGroupAnalysisResultField, SampleAnalysisResult, SampleAnalysisResultField)
class PangeaCoreAdmin(admin.ModelAdmin):
    pass

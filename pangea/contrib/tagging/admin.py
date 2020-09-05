from django.contrib import admin

from .models import (
    Tag,
    TagTagRelationship,
    SampleTagRelationship,
    SampleGroupTagRelationship,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'payload',)


@admin.register(TagTagRelationship)
class TagTagAdmin(admin.ModelAdmin):
    list_display = ('tag', 'other_tag', 'payload',)

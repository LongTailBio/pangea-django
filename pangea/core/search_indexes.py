
from haystack import indexes
from .models import (
    Organization,
    SampleGroup,
    Sample
)


class OrganizationIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    name = indexes.CharField(model_attr='name')

    def get_model(self):
        return Organization


class SampleGroupIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    name = indexes.CharField(model_attr='name')

    def get_model(self):
        return SampleGroup


class SampleIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    name = indexes.CharField(model_attr='name')

    def get_model(self):
        return Sample

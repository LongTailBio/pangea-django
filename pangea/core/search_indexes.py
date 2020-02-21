
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

    def prepare(self, object):
        self.prepared_data = super(SampleGroupIndex, self).prepare(object)
        self.prepared_data['org'] = object.organization.name
        return self.prepared_data


class SampleIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    name = indexes.CharField(model_attr='name')

    def get_model(self):
        return Sample

    def prepare(self, object):
        self.prepared_data = super(SampleGroupIndex, self).prepare(object)
        self.prepared_data['library'] = object.library.group.name
        return self.prepared_data

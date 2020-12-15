
from .organization import Organization
from .sample_group import SampleGroup
from .sample import Sample

from functools import lru_cache


def org_from_blob(knex, blob):
    org = Organization(knex, blob['name'])
    org.load_blob(blob)
    return org


def sample_group_from_blob(knex, blob):
    org = org_from_blob(knex, blob['organization_obj'])
    grp = SampleGroup(knex, org, blob['name'], is_library=blob['is_library'])
    grp.load_blob(blob)
    return grp


def sample_from_blob(knex, blob):
    lib = sample_group_from_blob(knex, blob['library_obj'])
    sample = Sample(knex, lib, blob['name'], metadata=blob['metadata'])
    sample.load_blob(blob)
    return sample


def sample_group_from_uuid(knex, uuid):
    blob = knex.get(f'sample_groups/{uuid}')
    sample = sample_group_from_blob(knex, blob)
    return sample


def sample_from_uuid(knex, uuid):
    blob = knex.get(f'samples/{uuid}')
    sample = sample_from_blob(knex, blob)
    return sample

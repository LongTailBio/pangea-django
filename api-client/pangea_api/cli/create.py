import click
import json
import pandas as pd

from requests.exceptions import HTTPError
from os import environ
from os.path import join, dirname
from os import makedirs

from .. import (
    Knex,
    User,
    Organization,
)
from ..blob_constructors import sample_from_uuid
from .utils import use_common_state


@click.group('create')
def cli_create():
    pass


@cli_create.command('org')
@use_common_state
@click.argument('org_name')
def cli_create_org(state, org_name):
    """Create an organization on Pangea."""
    knex = state.knex()
    org = Organization(knex, org_name).create()
    click.echo(f'Created: {org}', err=True)


@cli_create.command('sample-group')
@use_common_state
@click.option('--private/--public', default=True)
@click.option('--library/--not-library', default=True)
@click.argument('org_name')
@click.argument('grp_name')
def cli_create_grp(state, private, library, org_name, grp_name):
    """Create a sample group on Pangea."""
    knex = state.knex()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name, is_library=library, is_public=not private).create()
    click.echo(f'Created: {grp}', err=True)


@cli_create.command('samples')
@use_common_state
@click.option('-s', '--sample-names', default='-', type=click.File('r'))
@click.argument('org_name')
@click.argument('library_name')
def cli_create_samples(state, sample_names, org_name, library_name):
    """Create samples in the specified group.

    `sample_names` is a list of samples with one line per sample
    """
    knex = state.knex()
    org = Organization(knex, org_name).get()
    lib = org.sample_group(library_name, is_library=True).get()
    for sample_name in sample_names:
        sample_name = sample_name.strip()
        sample = lib.sample(sample_name).idem()
        print(sample, file=state.outfile)


@cli_create.command('sample-ar')
@use_common_state
@click.option('-r', '--replicate')
@click.argument('names', nargs=-1)
def cli_create_sample_ar(state, replicate, names):
    if len(names) not in [2, 4]:
        click.echo('''
            Names must be one of:
            <org name> <library name> <sample name> <new module name>
            <sample uuid> <new module name>
        ''', err=True)
        return
    knex = state.knex()
    module_name = names[-1]
    if len(names) == 2:
        sample = sample_from_uuid(knex, names[0])
    else:
        org = Organization(knex, names[0]).get()
        lib = org.sample_group(names[1]).get()
        sample = lib.sample(names[2]).get()
    ar = sample.analysis_result(module_name, replicate=replicate).create()
    click.echo(f'Created: {ar}', err=True)

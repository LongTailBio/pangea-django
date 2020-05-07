
import click
import json
from os import environ
from pangea_api import (
    Knex,
    User,
    Organization,
)

from .api import (
    auto_metadata,
    run_group,
    run_sample,
)


@click.group()
def main():
    """Pangea MetaGenScope."""
    pass


@main.group()
def run():
    """Run MetaGenScoep Middleware."""
    pass


@run.command('group')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-e', '--email', default=environ.get('PANGEA_USER', None))
@click.option('-p', '--password', default=environ.get('PANGEA_PASS', None))
@click.argument('org_name')
@click.argument('grp_name')
def cli_run_group(endpoint, email, password, org_name, grp_name):
    """Run MetaGenscope for a given group."""
    knex = Knex(endpoint)
    User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name).get()
    auto_metadata(list(grp.get_samples()), lambda x: click.echo(x, err=True))
    run_group(grp, lambda x: click.echo(x, err=True))


@run.command('samples')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-e', '--email', default=environ.get('PANGEA_USER', None))
@click.option('-p', '--password', default=environ.get('PANGEA_PASS', None))
@click.argument('org_name')
@click.argument('grp_name')
def cli_run_samples(endpoint, email, password, org_name, grp_name):
    """Run MetaGenscope for all samples in a given group."""
    knex = Knex(endpoint)
    User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name).get()
    for sample in grp.get_samples():
        try:
            run_sample(sample, lambda x: click.echo(x, err=True))
        except Exception as e:
            click.echo(f'Sample {sample.name} failed with exception: {e}')


@run.command('all')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-e', '--email', default=environ.get('PANGEA_USER', None))
@click.option('-p', '--password', default=environ.get('PANGEA_PASS', None))
@click.argument('org_name')
@click.argument('grp_name')
def cli_run_all(endpoint, email, password, org_name, grp_name):
    """Run MetaGenscope for a given group."""
    knex = Knex(endpoint)
    User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name).get()
    auto_metadata(list(grp.get_samples()), lambda x: click.echo(x, err=True))
    run_group(grp, lambda x: click.echo(x, err=True))
    for sample in grp.get_samples():
        try:
            run_sample(sample, lambda x: click.echo(x, err=True))
        except Exception as e:
            click.echo(f'Sample {sample.name} failed with exception: {e}')


@run.command('sample')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-e', '--email', default=environ.get('PANGEA_USER', None))
@click.option('-p', '--password', default=environ.get('PANGEA_PASS', None))
@click.argument('org_name')
@click.argument('grp_name')
@click.argument('sample_name')
def cli_run_sample(endpoint, email, password, org_name, grp_name, sample_name):
    """Register MetaGenScope for a Single Sample"""
    knex = Knex(endpoint)
    User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name).get()
    sample = grp.sample(sample_name).get()
    run_sample(sample, lambda x: click.echo(x, err=True))

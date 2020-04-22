
import click
from os import environ
from pangea_api import (
    Knex,
    User,
    Organization,
)
from .modules.top_taxa import TopTaxaModule


@click.group()
def main():
    pass


@main.group()
def run():
    pass


@run.command('group')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-e', '--email', default=environ.get('PANGEA_USER', None))
@click.option('-p', '--password', default=environ.get('PANGEA_PASS', None))
@click.argument('org_name')
@click.argument('grp_name')
def run_group(endpoint, email, password, org_name, grp_name):
    """Register a list of S3 URIs with Pangea."""
    knex = Knex(endpoint)
    User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name).get()
    if not TopTaxaModule.group_has_required_modules(grp):
        click.echo('Group does not meet requirements', err=True)
        return
    click.echo('Group meets requirements, processing', err=True)
    field = TopTaxaModule.process_group(grp)
    click.echo(field.stored_data)


@run.command('sample')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-e', '--email', default=environ.get('PANGEA_USER', None))
@click.option('-p', '--password', default=environ.get('PANGEA_PASS', None))
@click.argument('org_name')
@click.argument('grp_name')
@click.argument('sample_name')
def run_sample(endpoint, email, password, org_name, grp_name, sample_name):
    """Register a list of S3 URIs with Pangea."""
    knex = Knex(endpoint)
    User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name).get()
    sample = grp.sample(sample_name).get()
    if not TopTaxaModule.sample_has_required_modules(sample):
        click.echo('Sample does not meet requirements', err=True)
        return
    click.echo('Sample meets requirements, processing', err=True)
    field = TopTaxaModule.process_sample(sample)
    click.echo(field.stored_data)

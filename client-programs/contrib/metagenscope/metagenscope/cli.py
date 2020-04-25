
import click
import json
from os import environ
from pangea_api import (
    Knex,
    User,
    Organization,
)
from .modules import (
    TopTaxaModule,
    SampleSimilarityModule,
    AveGenomeSizeModule,
    AlphaDiversityModule,
    MultiAxisModule,
)

GROUP_MODULES = [
    MultiAxisModule,
    AlphaDiversityModule,
    TopTaxaModule,
    AveGenomeSizeModule,
    SampleSimilarityModule
]


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
    already_run = {ar.module_name for ar in grp.get_analysis_results()}
    for module in GROUP_MODULES:
        if module.name() in already_run:
            click.echo(f'Module {module.name()} has already been run for this group', err=True)
            continue
        if not module.group_has_required_modules(grp):
            click.echo(f'Group does not meet requirements for module {module.name()}', err=True)
            continue
        click.echo(f'Group meets requirements for module {module.name()}, processing', err=True)
        field = module.process_group(grp)
        field.idem()
        click.echo('done.', err=True)


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
    click.echo(json.dumps(field.stored_data))


import click
import json
import logging
from os import environ
from pangea_api import (
    Knex,
    User,
    Organization,
)
from pangea_api.contrib.tagging import Tag

from .api import (
    auto_metadata,
    run_group,
    run_sample,
)

logger = logging.getLogger(__name__)
      

@click.group()
def main():
    """Pangea MetaGenScope."""
    pass


@main.group()
def run():
    """Run MetaGenScoep Middleware."""
    pass


@run.command('group')
@click.option('-l', '--log-level', default=20)
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-e', '--email', default=environ.get('PANGEA_USER', None))
@click.option('-p', '--password', default=environ.get('PANGEA_PASS', None))
@click.argument('org_name')
@click.argument('grp_name')
def cli_run_group(log_level, endpoint, email, password, org_name, grp_name):
    """Run MetaGenscope for a given group."""
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s',
    )
    knex = Knex(endpoint)
    User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    logger.info(f'Loaded {org}')
    grp = org.sample_group(grp_name).get()
    logger.info(f'Loaded {grp}')
    auto_metadata(list(grp.get_samples()), grp)
    logger.info(f'Processed Metadata')
    run_group(grp, lambda x: click.echo(x, err=True))


@run.command('tag')
@click.option('-l', '--log-level', default=20)
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-e', '--email', envvar='PANGEA_USER')
@click.option('-p', '--password', envvar='PANGEA_PASS')
@click.option('-t', '--tag-name', default='MetaGenScope')
@click.option('--strict/--permissive', default=False)
def cli_process_tag(log_level, endpoint, email, password, tag_name, strict):
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s',
    )
    knex = Knex(endpoint)
    if email and password:
        User(knex, email, password).login()
    tag = Tag(knex, tag_name).get()
    for grp in tag.get_sample_groups():
        logger.info(f'Processing group {grp.name}')
        try:
            auto_metadata(list(grp.get_samples()), grp)
        except Exception as e:
            logger.warning(f'Autometa for group {grp.name} failed with exception: {e}')
            if strict:
                raise
        try:
            run_group(grp, strict=strict)
        except Exception as e:
            logger.warning(f'Group {grp.name} failed with exception: {e}')
            if strict:
                raise
        for sample in grp.get_samples():
            try:
                run_sample(sample, strict=strict)
            except Exception as e:
                logger.warning(f'Sample {sample.name} failed with exception: {e}')
                if strict:
                    raise


@run.command('samples')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-e', '--email', default=environ.get('PANGEA_USER', None))
@click.option('-p', '--password', default=environ.get('PANGEA_PASS', None))
@click.argument('org_name')
@click.argument('grp_name')
def cli_run_samples(endpoint, email, password, org_name, grp_name):
    """Run MetaGenscope for all samples in a given group."""
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s',
    )
    knex = Knex(endpoint)
    User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name).get()
    for sample in grp.get_samples():
        try:
            run_sample(sample)
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

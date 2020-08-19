
import click
import json
import pandas as pd

from os import environ
from os.path import join, dirname
from os import makedirs

from . import (
    Knex,
    User,
    Organization,
)


@click.group()
def main():
    pass


@main.group('list')
def cli_list():
    pass


@cli_list.command('samples')
@click.option('-e', '--email', envvar='PANGEA_USER')
@click.option('-p', '--password', envvar='PANGEA_PASS')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-o', '--outfile', default='-', type=click.File('w'))
@click.argument('org_name')
@click.argument('grp_name')
def cli_list_samples(email, password, endpoint, outfile, org_name, grp_name):
    """Print a list of samples in the specified group."""
    knex = Knex(endpoint)
    if email and password:
        User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name).get()
    for sample in grp.get_samples():
        print(sample, file=outfile)


@main.group('create')
def cli_create():
    pass


@cli_create.command('samples')
@click.option('-e', '--email', envvar='PANGEA_USER')
@click.option('-p', '--password', envvar='PANGEA_PASS')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-s', '--sample-names', default='-', type=click.File('r'))
@click.option('-o', '--outfile', default='-', type=click.File('w'))
@click.argument('org_name')
@click.argument('library_name')
def cli_create_samples(email, password, endpoint, sample_names, outfile, org_name, library_name):
    """Create samples in the specified group.

    `sample_names` is a list of samples with one line per sample
    """
    knex = Knex(endpoint)
    if email and password:
        User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    lib = org.sample_group(library_name, is_library=True).get()
    for sample_name in sample_names:
        sample_name = sample_name.strip()
        sample = lib.sample(sample_name).idem()
        print(sample, file=outfile)


@main.group('download')
def cli_download():
    pass


def _setup_download(email, password, endpoint, sample_manifest, org_name, grp_name, sample_names):
    knex = Knex(endpoint)
    if email and password:
        User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    grp = org.sample_group(grp_name).get()
    if sample_manifest:
        sample_names = set(sample_names) | set([el.strip() for el in sample_manifest if el])
    return grp, sample_names


@cli_download.command('metadata')
@click.option('-e', '--email', envvar='PANGEA_USER')
@click.option('-p', '--password', envvar='PANGEA_PASS')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-o', '--outfile', default='-', type=click.File('w'))
@click.option('--sample-manifest', type=click.File('r'),
              help='List of sample names to download from')
@click.argument('org_name')
@click.argument('grp_name')
@click.argument('sample_names', nargs=-1)
def cli_download_sample_results(email, password, endpoint, outfile, sample_manifest,
                                org_name, grp_name, sample_names):
    """Download Sample Analysis Results for a set of samples."""
    grp, sample_names = _setup_download(
        email, password, endpoint, sample_manifest, org_name, grp_name, sample_names
    )
    metadata = {}
    for sample in grp.get_samples(cache=False):
        if sample_names and sample.name not in sample_names:
            continue
        metadata[sample.name] = sample.metadata
    metadata = pd.DataFrame.from_dict(metadata, orient='index')
    metadata.to_csv(outfile)


@cli_download.command('sample-results')
@click.option('-e', '--email', envvar='PANGEA_USER')
@click.option('-p', '--password', envvar='PANGEA_PASS')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('--module-name')
@click.option('--field-name')
@click.option('--target-dir', default='.')
@click.option('--sample-manifest', default=None, type=click.File('r'),
              help='List of sample names to download from')
@click.argument('org_name')
@click.argument('grp_name')
@click.argument('sample_names', nargs=-1)
def cli_download_sample_results(email, password, endpoint, module_name, field_name, target_dir,
                                sample_manifest, org_name, grp_name, sample_names):
    """Download Sample Analysis Results for a set of samples."""
    grp, sample_names = _setup_download(
        email, password, endpoint, sample_manifest, org_name, grp_name, sample_names
    )
    for sample in grp.get_samples(cache=False):
        if sample_names and sample.name not in sample_names:
            continue
        for ar in sample.get_analysis_results(cache=False):
            if module_name and ar.module_name != module_name:
                continue
            for field in ar.get_fields(cache=False):
                if field_name and field.name != field_name:
                    continue
                filename = join(target_dir, field.get_blob_filename()).replace('::', '__')
                makedirs(dirname(filename), exist_ok=True)
                click.echo(f'Downloading BLOB {sample} :: {ar} :: {field} to {filename}', err=True)
                with open(filename, 'w') as blob_file:
                    blob_file.write(json.dumps(field.stored_data))
                try:
                    filename = join(target_dir, field.get_referenced_filename()).replace('::', '__')
                    click.echo(f'Downloading FILE {sample} :: {ar} :: {field} to {filename}', err=True)
                    field.download_file(filename=filename)
                except TypeError:
                    pass
                click.echo('done.', err=True)

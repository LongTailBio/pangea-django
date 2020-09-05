
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


@main.group('upload')
def cli_upload():
    pass


@cli_upload.command('reads')
@click.option('-e', '--email', envvar='PANGEA_USER')
@click.option('-p', '--password', envvar='PANGEA_PASS')
@click.option('--endpoint', default='https://pangea.gimmebio.com')
@click.option('-m', '--module-name', default='raw::raw_reads')
@click.option('-1', '--ext-1', default='.R1.fastq.gz')
@click.option('-2', '--ext-2', default='.R2.fastq.gz')
@click.option('-o', '--outfile', default='-', type=click.File('w'))
@click.argument('org_name')
@click.argument('library_name')
@click.argument('file_list', type=click.File('r'))
def cli_upload_reads(email, password, endpoint, module_name,
                     ext_1, ext_2, outfile, org_name, library_name, file_list):
    """Create samples in the specified group.

    `sample_names` is a list of samples with one line per sample
    """
    if not email or not password:
        click.echo('[WARNING] email or password not set.', err=True)
    knex = Knex(endpoint)
    if email and password:
        User(knex, email, password).login()
    org = Organization(knex, org_name).get()
    lib = org.sample_group(library_name).get()

    samples = {}
    for filepath in (l.strip() for l in file_list):
        if ext_1 in filepath:
            sname = filepath.split(ext_1)[0]
            key = 'read_1'
        if ext_2 in filepath:
            sname = filepath.split(ext_2)[0]
            key = 'read_2'
        sname = sname.split('/')[-1]
        if sname not in samples:
            samples[sname] = {}
        samples[sname][key] = filepath

    for sname, reads in samples.items():
        if len(reads) != 2:
            raise ValueError(f'Sample {sname} has wrong number of reads: {reads}')
        sample = lib.sample(sname).idem()
        ar = sample.analysis_result(module_name)
        r1 = ar.field('read_1').idem().upload_file(reads['read_1'], logger=lambda x: click.echo(x, err=True))
        r2 = ar.field('read_2').idem().upload_file(reads['read_2'], logger=lambda x: click.echo(x, err=True))
        print(sample, ar, r1, r2, file=outfile)


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
from .utils import use_common_state


@click.group('upload')
def cli_upload():
    pass


overwrite_option = click.option('--overwrite/--no-overwrite', default=False)
module_option = lambda x: click.option('-m', '--module-name', default=x)
private_option = click.option('--private/--public', default=True)
tag_option = click.option('-t', '--tag', multiple=True)

org_arg = click.argument('org_name')
lib_arg = click.argument('library_name')


@cli_upload.command('reads')
@use_common_state
@overwrite_option
@private_option
@tag_option
@module_option('raw::raw_reads')
@click.option('-d', '--delim', default=None, help='Split sample name on this character')
@click.option('-1', '--ext-1', default='.R1.fastq.gz')
@click.option('-2', '--ext-2', default='.R2.fastq.gz')
@org_arg
@lib_arg
@click.argument('file_list', type=click.File('r'))
def cli_upload_reads(state, overwrite, private, tag, module_name,
                     delim, ext_1, ext_2,
                     org_name, library_name, file_list):
    """Create samples in the specified group.

    `sample_names` is a list of samples with one line per sample
    """
    knex = state.get_knex()
    org = Organization(knex, org_name).get()
    lib = org.sample_group(library_name).get()
    tags = [Tag(knex, tag_name).get() for tag_name in tag]
    samples = {}
    for filepath in (l.strip() for l in file_list):
        if ext_1 in filepath:
            sname = filepath.split(ext_1)[0]
            key = 'read_1'
        if ext_2 in filepath:
            sname = filepath.split(ext_2)[0]
            key = 'read_2'
        sname = sname.split('/')[-1]
        if delim:
            sname = sname.split(delim)[0]
        if sname not in samples:
            samples[sname] = {}
        samples[sname][key] = filepath

    for sname, reads in samples.items():
        if len(reads) != 2:
            raise ValueError(f'Sample {sname} has wrong number of reads: {reads}')
        sample = lib.sample(sname).idem()
        for tag in tags:
            tag(sample)
        ar = sample.analysis_result(module_name)
        try:
            if overwrite:
                raise HTTPError()
            r1 = ar.field('read_1').get()
            r2 = ar.field('read_2').get()
        except HTTPError:
            ar.is_private = private
            r1 = ar.field('read_1').idem().upload_file(reads['read_1'], logger=lambda x: click.echo(x, err=True))
            r2 = ar.field('read_2').idem().upload_file(reads['read_2'], logger=lambda x: click.echo(x, err=True))
        print(sample, ar, r1, r2, file=state.outfile)


@cli_upload.command('single-ended-reads')
@use_common_state
@overwrite_option
@private_option
@tag_option
@module_option('raw::raw_single_ended_reads')
@click.option('-e', '--ext', default='.fastq.gz')
@org_arg
@lib_arg
@click.argument('file_list', type=click.File('r'))
def cli_upload_reads(state, overwrite, private, tag, module_name,
                     ext,
                     org_name, library_name, file_list):
    """Create samples in the specified group.

    `sample_names` is a list of samples with one line per sample
    """
    knex = state.get_knex()
    org = Organization(knex, org_name).get()
    lib = org.sample_group(library_name).get()
    tags = [Tag(knex, tag_name).get() for tag_name in tag]
    for filepath in (l.strip() for l in file_list):
        assert ext in filepath
        sname = filepath.split('/')[-1].split(ext)[0]
        sample = lib.sample(sname).idem()
        for tag in tags:
            tag(sample)
        ar = sample.analysis_result(module_name)
        try:
            if overwrite:
                raise HTTPError()
            reads = ar.field('reads').get()
        except HTTPError:
            ar.is_private = private
            reads = ar.field('reads').idem().upload_file(filepath, logger=lambda x: click.echo(x, err=True))
        print(sample, ar, reads, file=outfile)


@cli_upload.command('metadata')
@use_common_state
@overwrite_option
@click.option('--create/--no-create', default=False)
@click.option('--update/--no-update', default=False)
@click.option('--index-col', default=0)
@click.option('--encoding', default='utf_8')
@org_arg
@lib_arg
@click.argument('table', type=click.File('rb'))
def cli_metadata(state, overwrite,
                 create, update, index_col, encoding,
                 org_name, library_name, table):
    knex = state.get_knex()
    tbl = pd.read_csv(table, index_col=index_col, encoding=encoding)
    tbl.index = tbl.index.to_series().map(str)
    org = Organization(knex, org_name).get()
    lib = org.sample_group(library_name).get()
    for sample_name, row in tbl.iterrows():
        sample = lib.sample(sample_name)
        if create:
            sample = sample.idem()
        else:
            try:
                sample = sample.get()
            except Exception as e:
                click.echo(f'Sample "{sample.name}" not found.', err=True)
                continue
        new_meta = json.loads(json.dumps(row.dropna().to_dict())) 
        if overwrite or (not sample.metadata):
            sample.metadata = new_meta
            sample.idem()
        elif update:
            old_meta = sample.metadata
            old_meta.update(new_meta)
            sample.metadata = old_meta
            sample.idem()
        click.echo(sample)

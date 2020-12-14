
import click
import json
import pandas as pd

from pangea_api import (
    Knex,
    User,
    Organization,
)

from .api import sra_files_from_bioproject
from .bioproject import BioProject


@click.group()
def main():
    pass


@main.command('to-csv')
@click.option('-s', '--sleep', default=5)
@click.option('-o', '--outfile', type=click.File('w'), default='-')
@click.argument('accessions', nargs=-1)
def cli_to_csv(sleep, outfile, accessions):
    print('FOOOOOOo')
    tbls = []
    for accession in accessions:
        bioproj = BioProject(accession)
        tbls.append(bioproj.to_table(sleep=sleep)),
    tbl = pd.concat(tbls)
    tbl.to_csv(outfile)


@main.command('upload-csv')
@click.option('-e', '--email', envvar='PANGEA_USER')
@click.option('-p', '--password', envvar='PANGEA_PASS')
@click.option('-o', '--outfile', type=click.File('w'), default='-')
@click.argument('csv')
def cli_upload_csv(email, password, outfile, csv):
    knex = Knex('https://pangea.gimmebio.com')
    User(knex, email, password).login()
    org = Organization(knex, 'MegaGenome').idem()
    library = org.sample_group('SRA', is_library=True).idem()
    grps, samples = {}, {}
    tbl = pd.read_csv(csv)
    for _, row in tbl.iterrows():
        grp_name = str(row['bioproject'])
        try:
            grp = grps[grp_name]
        except KeyError:
            grp = org.sample_group(grp_name).idem()
            grps[grp_name] = grp
            click.echo(f'Created Group {grp}')
        sample_name = str(row['sra_rec'])
        try:
            sample = samples[sample_name]
            ar = sample.analysis_result('raw::raw_reads').get()
        except KeyError:
            sample = library.sample(sample_name).idem()
            ar = sample.analysis_result('raw::raw_reads').idem()
            grp.add_sample(sample).save()
            samples[sample_name] = sample
            click.echo(f'Created Sample {sample}')
            click.echo(f'Created AR {ar}')
        data = json.loads(row['sra_file_blob'])
        data['__type__'] = 'sra'
        ar.field(row['sra_file_kind'], data=data).idem()

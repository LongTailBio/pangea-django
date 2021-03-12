
import click
import random
import os
from glob import glob
from pangea_api import (
    Knex,
    Sample,
    Organization,
    SampleGroup,
    User,
    RemoteObjectError,
)
from pangea_api.work_orders import WorkOrderProto, WorkOrder, JobOrder
from cap2.api import run_modules
from cap2.sample import Sample
from cap2.constants import STAGES
from requests.exceptions import HTTPError

WORK_ORDER_PROTO_UUID = '385b7815-e3a7-4437-b173-0528bc37c719'


def random_str(len=12):
    """Return a random alphanumeric string of length `len`."""
    out = random.choices('abcdefghijklmnopqrtuvwxyzABCDEFGHIJKLMNOPQRTUVWXYZ0123456789', k=len)
    return ''.join(out)


def get_reads(sample):
    if sample.analysis_result('raw::raw_reads').exists():
        ar = sample.analysis_result('raw::raw_reads').get()
        r1 = ar.field('read_1').get()
        r2 = ar.field('read_2').get()
        r1_filepath = r1.download_file(filename=f'{sample.uuid}.R1.fq.gz')
        r2_filepath = r2.download_file(filename=f'{sample.uuid}.R2.fq.gz')
        cap_sample = Sample(sample.uuid, r1_filepath, r2_filepath)
        return cap_sample
    if sample.analysis_result('raw::paired_short_reads').exists():
        ar = sample.analysis_result('raw::paired_short_reads').get()
        r1 = ar.field('read_1').get()
        r2 = ar.field('read_2').get()
        r1_filepath = r1.download_file(filename=f'{sample.uuid}.R1.fq.gz')
        r2_filepath = r2.download_file(filename=f'{sample.uuid}.R2.fq.gz')
        cap_sample = Sample(sample.uuid, r1_filepath, r2_filepath)
        return cap_sample
    if sample.analysis_result('raw::single_short_reads').exists():
        ar = sample.analysis_result('raw::single_short_reads').get()
        r1 = ar.field('reads').get()
        r1_filepath = r1.download_file(filename=f'{sample.uuid}.R1.fq.gz')
        cap_sample = Sample(sample.uuid, r1_filepath)
        return cap_sample
    assert False  # could not find reads


def _process_fastqc(jo, sample):
    cap_sample = get_reads(sample)
    try:
        run_modules([cap_sample], STAGES['qc'])
        report = glob(f'results/{sample.uuid}/{sample.uuid}.cap2::fastqc.*.report.html')[0]
        zip_output = glob(f'results/{sample.uuid}/{sample.uuid}.cap2::fastqc.*.zip_out.zip')[0]
        ar = sample.analysis_result('cap2::fastqc', replicate=f'wo-demo {random_str(4)}').create()
        report_field = ar.field('report').create()
        report_field.upload_file(report)
        os.remove(report)
        zip_field = ar.field('zip_output').create()
        zip_field.upload_file(zip_output)
        os.remove(zip_output)
    finally:
        os.remove(sample.r1)
        if sample.r2:
            os.remove(sample.r2)


def process_fastqc(jo, sample):
    click.echo(f'Processing: {sample.name}')
    try:
        jo.status = 'working'
        jo.save()
        _process_fastqc(jo, sample)
        jo.status = 'success'
        jo.save()
    except Exception as e:
        jo.status = 'error'
        jo.save()
        click.echo(f'Failed: {sample.name}')
        click.echo(e)


def process_work_order(wo):
    jos = {jo.name: jo for jo in wo.get_job_orders()}
    fqc = jos['fastqc']
    sample = wo.get_sample()
    process_fastqc(fqc, sample)


@click.command()
@click.option('-e', '--email')
@click.option('-p', '--password')
def main(email, password):
    knex = Knex()
    User(knex, email, password).login()
    wop = WorkOrderProto.from_uuid(knex, WORK_ORDER_PROTO_UUID)
    for wo in wop.get_active_work_orders():
        if wo.status in ['success', 'working']:
            continue
        process_work_order(wo)


if __name__ == '__main__':
    main()

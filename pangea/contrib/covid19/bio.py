
import subprocess as sp
from os import environ
from os.path import isdir

KRAKEN2_EXC = 'kraken2'
KRAKEN2_DB = environ.get('COVID19_KRAKEN2_DB', None)
THREADS = int(environ.get('COVID19_THREADS', 1))
KRAKEN2_DB_URL = 'https://s3.wasabisys.com/metasub/covid/kraken2_covid_2020_03_13.tar.gz'


def download_kraken2():
    """Download a custom Kraken2 database for detecting COVID."""
    tarball_base = KRAKEN2_DB_URL.split("/")[-1]
    base = tarball_base.split('.tar.gz')[0]
    local_path = f'covid19/dbs/{base}'
    if isdir(local_path):
        return local_path
    cmd = (
        f'cd covid19/dbs/ && '
        f'wget {KRAKEN2_DB_URL} && '
        f'tar -xzf {tarball_base} '
    )
    sp.check_call(cmd, shell=True)
    return local_path


def kraken2_search_reads(reads, outprefix):
    """Use Kraken2 to make a fast pass report on reads. Write report to outfile."""
    reads = abspath(reads)
    report_filepath = f'{outprefix}.kraken2_report'
    kraken2_db = KRAKEN2_DB
    if kraken2_db is None:
        kraken2_db = download_kraken2()
    cmd = (
        f'{KRAKEN2_EXC} '
        f'--db {kraken2_db} '
        f'--threads {THREADS} '
        f'--report {report_filepath} '
        f'--gzip-compressed '
        f'{reads} '
        '> /dev/null'
    )
    sp.run(cmd, check=True, shell=True)
    return report_filepath

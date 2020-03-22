
import subprocess as sp
from os import environ

KRAKEN2_EXC = 'kraken2'
KRAKEN2_DB = environ['COVID19_KRAKEN2_DB']
THREADS = int(environ.get('COVID19_THREADS', 1))


def kraken2_search_reads(reads, outprefix):
    """Use Kraken2 to make a fast pass report on reads. Write report to outfile."""
    reads = abspath(reads)
    report_filepath = f'{outprefix}.kraken2_report'
    cmd = (
        f'{KRAKEN2_EXC} '
        f'--db {KRAKEN2_DB} '
        f'--threads {THREADS} '
        f'--report {report_filepath} '
        f'--report-zero-counts '
        f'--gzip-compressed '
        f'{reads}'
    )
    sp.run(cmd, check=True, shell=True)
    return report_filepath

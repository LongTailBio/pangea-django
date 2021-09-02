
import click
import logging

from ..contrib.tagging.cli import tag_main
from ..contrib.ncbi.cli import ncbi_main

from .add import cli_add
from .create import cli_create
from .download import cli_download
from .list import cli_list
from .upload import cli_upload
from .delete import cli_delete


logger = logging.getLogger('pangea_api')
logger.addHandler(logging.StreamHandler())


@click.group()
def main():
    pass


@main.command()
def version():
    """Print the version of the Pangea API being used."""
    click.echo('0.9.16')  # remember to update setup


main.add_command(tag_main)
main.add_command(ncbi_main)

main.add_command(cli_add)
main.add_command(cli_create)
main.add_command(cli_download)
main.add_command(cli_list)
main.add_command(cli_upload)
main.add_command(cli_delete)

import click

from .utils import use_common_state
from .constants import *


@click.group('delete')
def cli_delete():
    pass


@cli_delete.command('sample')
@use_common_state
@click.argument('uuid')
def cli_delete_sample(state, uuid):
	knex = state.get_knex()
	r = knex.delete(f'samples/{uuid}', json_response=False)
	click.echo(f'deleted sample {uuid}', err=True)


@cli_delete.command('group')
@use_common_state
@click.argument('uuid')
def cli_delete_sample(state, uuid):
	knex = state.get_knex()
	r = knex.delete(f'sample_groups/{uuid}', json_response=False)
	click.echo(f'deleted sample group {uuid}', err=True)


@cli_delete.command('sample-result')
@use_common_state
@click.argument('uuid')
def cli_delete_sample(state, uuid):
	knex = state.get_knex()
	r = knex.delete(f'sample_ars/{uuid}', json_response=False)
	click.echo(f'deleted sample result {uuid}', err=True)


@cli_delete.command('group-result')
@use_common_state
@click.argument('uuid')
def cli_delete_sample(state, uuid):
	knex = state.get_knex()
	r = knex.delete(f'sample_group_ars/{uuid}', json_response=False)
	click.echo(f'deleted sample group result {uuid}', err=True)

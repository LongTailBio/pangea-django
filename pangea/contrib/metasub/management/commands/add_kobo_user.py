
import sys

from django.core.management.base import BaseCommand
from pangea.contrib.metasub.models import KoboUser
from pangea.contrib.metasub.kobo_map import refresh_kobo_user


class Command(BaseCommand):
    help = 'Add a Kobo User and populate assets and results'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password')

    def handle(cls, *args, **kwargs):
        """Populate database tables with taxonomic info."""
        kobo_user = KoboUser(username=kwargs['username'], password=kwargs['password'])
        kobo_user.save()
        refresh_kobo_user(kobo_user)

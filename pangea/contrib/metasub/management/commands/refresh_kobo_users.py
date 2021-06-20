
import sys

from django.core.management.base import BaseCommand
from pangea.contrib.metasub.models import KoboUser
from pangea.contrib.metasub.kobo_map import refresh_kobo_user


class Command(BaseCommand):
    help = 'Refresh a Kobo User and populate assets and results'


    def handle(cls, *args, **kwargs):
        """Populate database tables with taxonomic info."""
        for kobo_user in KoboUser.objects.all():
        	refresh_kobo_user(kobo_user)

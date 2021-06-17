
import sys
import pandas as pd

from django.core.management.base import BaseCommand
from pangea.contrib.metasub.models import MetaSUBCity
from pangea.contrib.metasub.constants import CITY_INFO_PATH


class Command(BaseCommand):
    help = 'Populate cities for MetaSUB'

    def handle(cls, *args, **kwargs):
    	tbl = pd.read_csv(CITY_INFO_PATH)
    	for i, row, in tbl.iterrows():
    		city = MetaSUBCity(
    			name=row['City'].lower().replace(' ', '_'),
    			display_name=row['City'],
    			latitude=row['latitude'],
    			longitude=row['longitude'],
    		)
    		city.save()
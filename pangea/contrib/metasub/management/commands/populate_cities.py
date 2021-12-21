
import sys
import pandas as pd

from django.core.management.base import BaseCommand
from pangea.contrib.metasub.models import MetaSUBCity
from pangea.contrib.metasub.constants import CITY_INFO_PATH, CITY_INFO_2_PATH


class Command(BaseCommand):
    help = 'Populate cities for MetaSUB'

    def handle(cls, *args, **kwargs):
    	tbl2 = pd.read_csv(CITY_INFO_2_PATH)
    	names = set()
    	for i, row, in tbl2.iterrows():
    		city = MetaSUBCity(
    			name=row['name'],
    			display_name=row['name_full'],
    			latitude=row['lat'],
    			longitude=row['lon'],
    		)
    		city.save()
    		names.add(row['name'])
    	tbl = pd.read_csv(CITY_INFO_PATH)
    	for i, row, in tbl.iterrows():
    		name = row['City'].lower().replace(' ', '_').replace(',', '')
    		if name in names:
    			continue
    		city = MetaSUBCity(
    			name=name,
    			display_name=row['City'],
    			latitude=row['latitude'],
    			longitude=row['longitude'],
    		)
    		city.save()
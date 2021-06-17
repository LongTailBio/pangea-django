
from pangea.core.models import SampleGroup
from os.path import join, dirname

METASUB_ORG_NAME = 'MetaSUB Consortium'
METASUB_GRP_NAME = 'MetaSUB'

METASUB_LIBRARY = lambda: SampleGroup.objects.get(name=METASUB_GRP_NAME)
METASUB_LIBRARY_UUID = lambda: METASUB_LIBRARY().uuid


CITY_INFO_PATH = join(dirname(__file__), 'metasub_city_info.csv')
CITY_INFO_2_PATH = join(dirname(__file__), 'metasub_city_info_2.csv')
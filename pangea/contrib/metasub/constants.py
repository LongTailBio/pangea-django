
from pangea.core.models import SampleGroup

METASUB_ORG_NAME = 'MetaSUB Consortium'
METASUB_GRP_NAME = 'MetaSUB'

METASUB_LIBRARY_UUID = lambda: SampleGroup.objects.get(name=METASUB_GRP_NAME).uuid

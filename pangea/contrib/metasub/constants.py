
from pangea.core.models import SampleGroup

METASUB_ORG_NAME = 'MetaSUB Consortium'
METASUB_GRP_NAME = 'MetaSUB'

METASUB_LIBRARY = lambda: SampleGroup.objects.get(name=METASUB_GRP_NAME)
METASUB_LIBRARY_UUID = lambda: METASUB_LIBRARY().uuid

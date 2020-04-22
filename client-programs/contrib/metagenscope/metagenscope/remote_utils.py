
from urllib.request import urlretrieve
from tempfile import NamedTemporaryFile


def download_s3_file(blob):
    """Download an s3file and return a local path."""
    try:
        url = blob['presigned_url']
    except KeyError:
        url = blob['uri']
    if url.startswith('s3://'):
        url = blob['endpoint_url'] + '/' + url[5:]
    myfile = NamedTemporaryFile(delete=False)
    myfile.close()
    urlretrieve(url, myfile.name)
    return myfile.name

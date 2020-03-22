from contextlib import contextmanager
import os
import re
import structlog
import tempfile
from urllib.parse import urlparse

from django.conf import settings
import boto3
from botocore.exceptions import ClientError


logger = structlog.get_logger(__name__)


def parse_object_uri(cloud_uri):
    """Parse the bucket and object path from a cloud URI."""
    parsed_url = urlparse(cloud_uri)
    bucket = None
    object_name = None

    # Handle the s3://bucket/path/to/object form
    if (re.match(r'^s3:\/\/.*', cloud_uri)):
        bucket = parsed_url.netloc
        object_name = parsed_url.path.lstrip('/')

    # Handle the https://s3.wasabisys.com/bucket/path/to/object form
    elif match := re.match(r'^\/(.+?)\/(.+)$', parsed_url.path):
        bucket = match.group(1)
        object_name = match.group(2)

    if bucket is None or object_name is None:
        logger.info('invalid_cloud_uri', cloud_uri=cloud_uri, bucket=bucket, object_name=object_name)
        raise Exception('Invalid cloud storage URI')

    return bucket, object_name


s3 = boto3.client(
    's3',
    endpoint_url = settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
)


@contextmanager
def cloud_file_path(cloud_uri):
    """Download and cleanup of cloud storage object."""
    bucket, object_name = parse_object_uri(cloud_uri)

    # Manage file lifecycle ourselves to allow another process to consume it
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_name = temp_file.name
        s3.download_fileobj(bucket, object_name, temp_file)
        temp_file.close()
        yield temp_name
    finally:
        os.unlink(temp_name)


def upload_file(file_name, bucket=None, object_name=None):
    """Upload a file to cloud storage."""
    if bucket is None:
        bucket = settings.S3_BUCKET
    if object_name is None:
        object_name = file_name

    s3.upload_file(file_name, bucket, object_name)


def create_presigned_url(object_name, bucket=None, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    if bucket is None:
        bucket = settings.S3_BUCKET

    try:
        response = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': object_name},
            ExpiresIn=expiration
        )
        # The response contains the presigned URL
        return response
    except ClientError as e:
        logger.error(e)
        return None

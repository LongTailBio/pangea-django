from background_task import background
from django.core.mail import send_mail
import structlog
import tempfile

from pangea.core.models import PangeaUser, Sample, SampleAnalysisResult, SampleAnalysisResultField

from .utils import cloud_file_path, upload_file, create_presigned_url
from .bio import kraken2_search_reads

logger = structlog.get_logger(__name__)


@background(queue='covid19', schedule=60)
def process_covid19(user_id, reads_path):
    """Process covid19 raw reads and upload result to AWS S3."""
    logger.info(
        'covid19_process_raw_reads',
        user_id=user_id,
        reads_path=reads_path
    )

    with cloud_file_path(reads_path) as temp_file_path:
        logger.info('fetched_temp_cloud_storage_file', temp_file_path=temp_file_path)

        result_filepath = kraken2_search_reads(temp_file_path, f'{user_id}_covid19_results')
        logger.info('ran_kraken2', result_filepath=result_filepath)
        results_object_name = f'covid19/results/{result_filepath}'
        upload_file(result_filepath, object_name=results_object_name)

        # One week expiration
        expiration = 60 * 60 * 24 * 7
        presigned_url = create_presigned_url(results_object_name, expiration=expiration)
        user = PangeaUser.objects.get(pk=user_id)
        try:
            # TODO: tweak email copy
            send_mail(
                'Your Pangea COVID-19 Results',
                f'Your results are ready. They can be accessed at the following URL for the next week:\n\n{presigned_url}\n\nBest,\nThe Pangea Team',
                'no-reply@pangea.gimmebio.com',
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.exception('send_mail_exception', user_id=user.id, user_email=user.email)

        # TODO: Upsert analysis result field

from background_task import background
from django.core.mail import send_mail
import structlog
import tempfile

from pangea.core.models import PangeaUser, Sample, SampleAnalysisResult, SampleAnalysisResultField

from .utils import cloud_file_path, upload_file, create_presigned_url


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

        results_object_name = f'covid19/results/{user_id}.txt'

        # TODO: perform analysis
        analysis_results = f'[COVID-19 result for user {user_id}]'

        # Upload the result to cloud storage
        with tempfile.NamedTemporaryFile('w') as results_file:
            results_file.write(analysis_results)
            results_file.flush()
            upload_file(results_file.name, object_name=results_object_name)

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

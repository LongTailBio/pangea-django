from background_task import background
import structlog
import tempfile

from pangea.core.models import Sample, SampleAnalysisResult, SampleAnalysisResultField

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

        # TODO: notify user via email
        presigned_url = create_presigned_url(results_object_name)
        logger.info('covid19_placeholder_notify_user', presigned_url=presigned_url)

        # TODO: Upsert analysis result field

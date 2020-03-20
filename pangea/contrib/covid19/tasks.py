from background_task import background
import structlog

from pangea.core.models import Sample, SampleAnalysisResult, SampleAnalysisResultField


logger = structlog.get_logger(__name__)


@background(queue='covid19', schedule=60)
def process_covid19(user_id, reads_path):
    """Process covid19 raw reads and upload result to AWS S3."""
    logger.info(
        'covid19_process_raw_reads',
        user_id=user_id,
        reads_path=reads_path
    )

    # TODO: fetch raw reads

    # TODO: perform analysis

    # TODO: upload the result to cloud storage
    cloud_storage_path = 's3://covid-19-bucket/results/result.pdf'

    # TODO: notify user via email

    # TODO: Upsert analysis result field

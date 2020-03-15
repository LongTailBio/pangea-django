from background_task import background
import structlog

from pangea.core.models import Sample, SampleAnalysisResult, SampleAnalysisResultField


logger = structlog.get_logger(__name__)


@background(queue='covid19', schedule=60)
def process_covid19(sample_uuid, reads_path):
    """Process covid19 raw reads and upload result to AWS S3."""
    with open(reads_path, 'rb+') as raw_reads:
        # TODO: run analyses and generate result
        pass

    # TODO: upload the result to cloud storage
    cloud_storage_path = 's3://covid-19-bucket/results/result.pdf'

    # Upsert analysis result field
    sample = Sample.objects.get(pk=sample_uuid)
    result, result_created = SampleAnalysisResult.objects.get_or_create(sample=sample, module_name='covid19')
    field, field_created = SampleAnalysisResultField.objects.get_or_create(
        analysis_result=result,
        name='cloud_result',
        defaults={ 'stored_data': {} }
    )
    field.stored_data = { 'cloud_storage_path': cloud_storage_path }
    field.save()

    logger.info(
        'stored_covid19_results',
        sample_uuid=sample_uuid,
        cloud_storage_path=cloud_storage_path,
    )

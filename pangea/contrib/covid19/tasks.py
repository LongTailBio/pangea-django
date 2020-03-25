from background_task import background
from django.core.mail import send_mail
import structlog
import tempfile

from django.conf import settings
from pangea.core.models import PangeaUser, Sample, SampleAnalysisResult, SampleAnalysisResultField
from pangea.core.utils import random_replicate_name

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
        sample_name = reads_path.split('/')[-1].split('.fq')[0].split('.fastq')[0]
        replicate = random_replicate_name()

        result_filepath = kraken2_search_reads(
            temp_file_path,
            f'{sample_name}.{replicate}.covid19_results'
        )
        logger.info('ran_kraken2', result_filepath=result_filepath)
        results_object_name = f'covid19/results/{result_filepath}'
        upload_file(result_filepath, object_name=results_object_name)

        user = PangeaUser.objects.get(pk=user_id)
        grp = user.personal_org.core_sample_group
        sample = grp.create_sample(name=sample_name)
        sample.save()
        ar = sample.create_analysis_result(
            module_name='covid19_kraken2',
            replicate=replicate,
        )
        ar.save()
        field = ar.create_field(name='report', stored_data={
            '__type__': 's3',
            'endpoint_url': settings.S3_ENDPOINT,
            'uri': f's3://{settings.S3_BUCKET}/{results_object_name}', 
        })
        field.save()

        # One week expiration
        expiration = 60 * 60 * 24 * 7
        presigned_url = create_presigned_url(results_object_name, expiration=expiration)
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

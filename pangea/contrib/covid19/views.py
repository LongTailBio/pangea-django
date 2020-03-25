from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
import structlog

from .serializers import Covid19ReadsUploadSerializer
from .tasks import process_covid19


logger = structlog.get_logger(__name__)


class Covid19ListCreateView(APIView):
    """Handle listing all covid19 results."""

    serializer_class = Covid19ReadsUploadSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle upload of covid19 raw reads.
        
        We implement our own post method so that we can return a custom object type with the task ID
        """
        serializer = Covid19ReadsUploadSerializer(data=request.data)

        if (serializer.is_valid()):
            reads_user = serializer.validated_data.get('user')
            raw_reads_path = serializer.validated_data.get('raw_reads_path')

            if request.user.id != reads_user.id:
                raise PermissionDenied(_('Users may only upload their own covid19 reads.'))

            logger.info(
                'covid19_raw_reads_received',
                auth_user=request.user.email,
                raw_reads_path=raw_reads_path,
            )

            # Kick off background processing task
            task = process_covid19(reads_user.id, raw_reads_path)

            return Response({ 'status': 'success', 'task_hash': task.task_hash }, 201)
        else:
            return Response(serializer.errors, status=400)

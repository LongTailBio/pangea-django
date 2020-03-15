import time

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
import structlog

from .serializers import Covid19ReadsUploadSerializer


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
            organization = serializer.validated_data.get('sample').library.group.organization
            membership_queryset = request.user.organization_set.filter(pk=organization.pk)
            if not membership_queryset.exists():
                raise PermissionDenied(_('Organization membership is required to upload covid19 reads.'))

            # Store and process the file
            raw_reads = serializer.validated_data.get('raw_reads')
            sample_uuid = str(serializer.validated_data.get('sample').uuid)
            reads_path = f'{settings.MEDIA_ROOT}covid19-{sample_uuid}-{int(time.time())}-{str(raw_reads)}'
            with open(reads_path, 'wb+') as destination:
                for chunk in raw_reads.chunks():
                    destination.write(chunk)

            logger.info(
                'covid19_reads_stored',
                auth_user=request.user.email,
                sample_uuid=sample_uuid,
                path=reads_path,
            )

            # TODO: kick off background task
            return Response({ 'status': 'success', 'task_id': 1 }, 201)
        else:
            return Response(serializer.errors, status=400)

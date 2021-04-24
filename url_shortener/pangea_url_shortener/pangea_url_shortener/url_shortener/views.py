from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ShortenedUrl


@api_view(['GET'])
def get_redirect(request, name):
    try:
        short = ShortenedUrl.objects.get(name=name)
    except:
        return Response(status=404)
    short.hit_count += 1
    short.save()
    response = Response(status=302, headers={'Location': short.target})
    return response

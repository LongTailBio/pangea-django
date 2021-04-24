from django.urls import path

from .views import get_redirect

urlpatterns = [
    path('<name>', get_redirect, name='get-redirect'),
]

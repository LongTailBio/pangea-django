"""pangea URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.contrib import admin
from django.urls import path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('pangea.core.urls')),
    path('api/nested/', include('pangea.core.nested_urls')),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/contrib/covid19/', include('pangea.contrib.covid19.urls')),
    path('api/contrib/metasub/', include('pangea.contrib.metasub.urls')),
    path('api/contrib/taxasearch/', include('pangea.contrib.taxasearch.urls')),
    path('api/contrib/treeoflife/', include('pangea.contrib.treeoflife.urls')),
]

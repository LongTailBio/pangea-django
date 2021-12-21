from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import uuid
import random
import structlog
import requests

from pangea.core.mixins import AutoCreatedUpdatedMixin
from .utils import (
    paginated_iterator,
    get_project,
)


class KoboAsset(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kobo_id = models.TextField(editable=False, unique=True)
    name = models.TextField(blank=False)
    description = models.TextField(blank=False)
    kobo_user = models.ForeignKey(
        'KoboUser', on_delete=models.CASCADE, related_name='kobo_assets'
    )
    project = models.TextField()
    city = models.ForeignKey(
        'MetaSUBCity', on_delete=models.CASCADE, related_name='kobo_assets'
    )

    def get_results(self):
        initial_url = f'https://kf.kobotoolbox.org/api/v2/assets/{self.kobo_id}/data.json'
        getter = lambda url: requests.get(url, headers={'Authorization': f'Token {self.kobo_user.token}'})
        for result_blob in paginated_iterator(getter, initial_url):
            kobo_id = result_blob['_id']
            if KoboResult.objects.filter(kobo_id=kobo_id).exists():
                continue
            result = KoboResult(
                kobo_asset=self,
                kobo_id=kobo_id,
                data=result_blob,
            )
            result.save()

    def __str__(self):
        return f'<KoboAsset name={self.name} kobo_id={self.kobo_id} />'


class MetaSUBCity(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    display_name = models.TextField(blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f'<MetaSUBCity name={self.name} />'


def get_or_create_city(name):
    city_names = {city.name: city for city in MetaSUBCity.objects.all()}
    name = name.lower().replace(' ', '_')
    for city_name, city in city_names.items():
        if city_name in name:
            return city
    obj = MetaSUBCity(name=name)
    obj.save()
    return obj


class KoboUser(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.TextField(blank=False)
    password = models.TextField(blank=False)
    token = models.TextField(blank=True)

    def refresh_token(self):
        url = f'https://{self.username}:{self.password}@kf.kobotoolbox.org/token/?format=json'
        response = requests.get(url)
        response.raise_for_status()
        blob = response.json()
        self.token = blob['token']
        self.save()

    def get_assets(self):
        initial_url = 'https://kf.kobotoolbox.org/api/v2/assets.json'
        getter = lambda url: requests.get(url, headers={'Authorization': f'Token {self.token}'})
        for asset_blob in paginated_iterator(getter, initial_url):
            kobo_id = asset_blob['uid']
            if KoboAsset.objects.filter(kobo_id=kobo_id).exists():
                continue
            asset = KoboAsset(
                kobo_id=kobo_id,
                name=asset_blob['name'],
                description=asset_blob.get('settings', {}).get('description', ''),
                kobo_user=self,
                project=get_project(asset_blob['name']),
                city=get_or_create_city(asset_blob['name'].split('_')[-1]),
            )
            asset.save()

    def __str__(self):
        return f'<KoboUser username={self.username} />'


class KoboResult(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kobo_id = models.TextField(editable=False, unique=True)
    kobo_asset = models.ForeignKey(
        'KoboAsset', on_delete=models.CASCADE, related_name='kobo_results'
    )
    data = JSONField(blank=True, default=dict)

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


class KoboAsset(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kobo_id = models.TextField(editable=False)
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
        url = f'https://kf.kobotoolbox.org/api/v2/assets/{self.kobo_id}/data.json'
        response = requests.get(url, headers={'Authorization': f'Token {self.kobo_user.token}'})
        response.raise_for_status()
        blob = response.json()
        for result_blob in blob['results']:
            result = KoboResult(
                kobo_asset=self,
                kobo_id=result_blob['_id'],
                data=result_blob,
            )
            result.save()

    def __str__(self):
        return f'<KoboAsset name={self.name} kobo_id={self.kobo_id} />'


class MetaSUBCity(AutoCreatedUpdatedMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    display_name = models.TextField(blank=True)
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)

    def __str__(self):
        return f'<MetaSUBCity name={self.name} />'

def get_project(text):
    text = text.lower()
    for x in ['gcsd16', 'gcsd17', 'gcsd18', 'gcsd19', 'gcsd20', 'gcsd21']:
        if x in text:
            return x
    return 'unknown'


def get_or_create_city(name):
    name = name.lower().replace(' ', '_')
    obj = MetaSUBCity.objects.filter(name=name)
    if obj.exists():
        return obj.get()
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
        url = 'https://kf.kobotoolbox.org/api/v2/assets.json'
        response = requests.get(url, headers={'Authorization': f'Token {self.token}'})
        response.raise_for_status()
        blob = response.json()
        for asset_blob in blob['results']:
            asset = KoboAsset(
                kobo_id=asset_blob['uid'],
                name=asset_blob['name'],
                description=asset_blob['settings']['description'],
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

from django.db import models

# Create your models here.


class ShortenedUrl(models.Model):

    name = models.TextField(blank=False, unique=True)
    target = models.TextField(blank=False, unique=False)
    hit_count = models.IntegerField(blank=False, default=0)

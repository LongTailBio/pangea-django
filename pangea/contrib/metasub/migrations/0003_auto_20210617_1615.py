# Generated by Django 3.0.3 on 2021-06-17 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metasub', '0002_auto_20210617_1612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metasubcity',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='metasubcity',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
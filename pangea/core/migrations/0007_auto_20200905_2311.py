# Generated by Django 3.0.3 on 2020-09-05 23:11

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import pangea.core.encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20200905_2245'),
    ]

    operations = [
        migrations.AddField(
            model_name='sample',
            name='description',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='sampleanalysisresult',
            name='description',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='samplegroup',
            name='long_description',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='samplegroup',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='samplegroupanalysisresult',
            name='description',
            field=models.TextField(default=''),
        ),
    ]

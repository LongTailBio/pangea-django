# Generated by Django 3.0.3 on 2021-01-22 15:22

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import pangea.core.encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20201228_1649'),
    ]

    operations = [
        migrations.CreateModel(
            name='VersionedMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('sample', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='versioned_metadata', to='core.Sample')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
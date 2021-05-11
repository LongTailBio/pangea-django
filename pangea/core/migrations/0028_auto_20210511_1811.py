# Generated by Django 3.0.3 on 2021-05-11 18:11

from django.db import migrations, models
import django.db.models.deletion
import pangea.core.encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_auto_20210511_1733'),
    ]

    operations = [
        migrations.CreateModel(
            name='PipelineWiki',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('pipeline', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='wiki', serialize=False, to='core.Pipeline')),
                ('wiki', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='core.Wiki')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrganizationWiki',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='wiki', serialize=False, to='core.Organization')),
                ('wiki', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='core.Wiki')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

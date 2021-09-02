# Generated by Django 3.0.3 on 2021-03-11 03:27

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import pangea.core.encrypted_fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20210301_2236'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkOrderProto',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField(db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkOrder',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField(db_index=True)),
                ('priority', models.IntegerField(default=100)),
                ('prototype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.WorkOrderProto')),
                ('sample', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_orders', to='core.Sample')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PrivilegedUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('work_order_proto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='privileged_users', to='core.WorkOrderProto')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='JobOrderProto',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField(db_index=True)),
                ('resources_needed', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('pipeline_module', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_order_protos', to='core.PipelineModule')),
                ('work_order_proto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_protos', to='core.WorkOrderProto')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='JobOrder',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField(db_index=True)),
                ('status', models.TextField(choices=[('pending', 'Pending'), ('error', 'Error'), ('working', 'Working'), ('success', 'Success')], default='pending')),
                ('resources_used', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('resources_needed', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
                ('analysis_result', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_order', to='core.SampleAnalysisResult')),
                ('pipeline_module', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_orders', to='core.PipelineModule')),
                ('prototype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.JobOrderProto')),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='core.WorkOrder')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

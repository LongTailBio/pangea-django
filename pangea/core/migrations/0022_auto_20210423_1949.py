# Generated by Django 3.0.3 on 2021-04-23 19:49

from django.db import migrations, models
import django.db.models.deletion
import pangea.core.encrypted_fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_auto_20210312_1848'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupWorkOrderProto',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField(db_index=True)),
                ('description', models.TextField(blank=True, default='')),
                ('work_order_protos', models.ManyToManyField(blank=True, null=True, to='core.WorkOrderProto')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GroupWorkOrder',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField(db_index=True)),
                ('priority', models.IntegerField(default=100)),
                ('description', models.TextField(blank=True, default='')),
                ('prototype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.GroupWorkOrderProto')),
                ('sample_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_orders', to='core.SampleGroup')),
                ('work_orders', models.ManyToManyField(blank=True, null=True, to='core.WorkOrder')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

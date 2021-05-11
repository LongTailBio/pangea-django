# Generated by Django 3.0.3 on 2021-04-26 17:25

from django.db import migrations, models
import django.db.models.deletion
import pangea.core.encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_merge_20210424_2147'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='cached_status',
            field=models.TextField(choices=[('pending', 'Pending'), ('error', 'Error'), ('working', 'Working'), ('success', 'Success')], default='pending'),
        ),
    ]
# Generated by Django 3.0.3 on 2021-05-11 17:33

from django.db import migrations, models
import django.db.models.deletion
import pangea.core.encrypted_fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_auto_20210511_1428'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wikipage',
            name='title',
            field=models.TextField(),
        ),
    ]
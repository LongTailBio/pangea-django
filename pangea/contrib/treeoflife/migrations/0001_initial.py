# Generated by Django 3.0.3 on 2020-03-28 23:46

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TaxonName',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('taxon_id', models.TextField(db_index=True, editable=False)),
                ('name', models.TextField(db_index=True)),
                ('name_type', models.TextField(db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TreeNode',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('taxon_id', models.TextField(db_index=True, editable=False)),
                ('rank', models.TextField(db_index=True)),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='treeoflife.TreeNode')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Virus',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('human_commensal', models.TextField()),
                ('antimicrobial_susceptibility', models.TextField()),
                ('optimal_temperature', models.TextField()),
                ('extreme_environment', models.TextField()),
                ('optimal_ph', models.TextField()),
                ('animal_pathogen', models.TextField()),
                ('spore_forming', models.TextField()),
                ('pathogenicity', models.TextField()),
                ('plant_pathogen', models.TextField()),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('taxon_id', models.TextField(db_index=True, editable=False)),
                ('virus_name', models.TextField()),
                ('virus_lineage', models.TextField()),
                ('kegg_genome', models.TextField()),
                ('kegg_disease', models.TextField()),
                ('disease', models.TextField()),
                ('host_name', models.TextField()),
                ('host_lineage', models.TextField()),
                ('tree_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='virus_annotation_set', to='treeoflife.TreeNode', unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Fungi',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('human_commensal', models.TextField()),
                ('antimicrobial_susceptibility', models.TextField()),
                ('optimal_temperature', models.TextField()),
                ('extreme_environment', models.TextField()),
                ('optimal_ph', models.TextField()),
                ('animal_pathogen', models.TextField()),
                ('spore_forming', models.TextField()),
                ('pathogenicity', models.TextField()),
                ('plant_pathogen', models.TextField()),
                ('salinity_concentration_range_w_v', models.TextField()),
                ('biofilm_forming', models.TextField()),
                ('halotolerance', models.TextField()),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('taxon_id', models.TextField(db_index=True, editable=False)),
                ('tree_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fungi_annotation_set', to='treeoflife.TreeNode', unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Bacteria',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('human_commensal', models.TextField()),
                ('antimicrobial_susceptibility', models.TextField()),
                ('optimal_temperature', models.TextField()),
                ('extreme_environment', models.TextField()),
                ('optimal_ph', models.TextField()),
                ('animal_pathogen', models.TextField()),
                ('spore_forming', models.TextField()),
                ('pathogenicity', models.TextField()),
                ('plant_pathogen', models.TextField()),
                ('salinity_concentration_range_w_v', models.TextField()),
                ('biofilm_forming', models.TextField()),
                ('halotolerance', models.TextField()),
                ('low_ph', models.TextField()),
                ('high_ph', models.TextField()),
                ('drylands', models.TextField()),
                ('low_productivity', models.TextField()),
                ('gram_stain', models.TextField()),
                ('psychrophilic', models.TextField()),
                ('radiophilic', models.TextField()),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('taxon_id', models.TextField(db_index=True, editable=False)),
                ('tree_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bacteria_annotation_set', to='treeoflife.TreeNode', unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Archaea',
            fields=[
                ('created_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('human_commensal', models.TextField()),
                ('antimicrobial_susceptibility', models.TextField()),
                ('optimal_temperature', models.TextField()),
                ('extreme_environment', models.TextField()),
                ('optimal_ph', models.TextField()),
                ('animal_pathogen', models.TextField()),
                ('spore_forming', models.TextField()),
                ('pathogenicity', models.TextField()),
                ('plant_pathogen', models.TextField()),
                ('salinity_concentration_range_w_v', models.TextField()),
                ('biofilm_forming', models.TextField()),
                ('halotolerance', models.TextField()),
                ('low_ph', models.TextField()),
                ('high_ph', models.TextField()),
                ('drylands', models.TextField()),
                ('low_productivity', models.TextField()),
                ('gram_stain', models.TextField()),
                ('psychrophilic', models.TextField()),
                ('radiophilic', models.TextField()),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('taxon_id', models.TextField(db_index=True, editable=False)),
                ('tree_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archaea_annotation_set', to='treeoflife.TreeNode', unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

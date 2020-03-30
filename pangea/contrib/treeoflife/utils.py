
from django.core.exceptions import ObjectDoesNotExist
from microbe_directory import (
    bacteria,
    eukaryote,
    virus,
    md1,
)

from .models import (
    Bacteria,
    Archaea,
    Fungi,
    Virus,
    TreeNode
)


def save_virus(tree_node, row):
    Virus(
        tree_node=tree_node,
        taxon_id=str(row['taxonomic_id']).strip(),
        virus_name=row['virus_name'],
        virus_lineage=row['virus_lineage'],
        kegg_genome=row['kegg_genome'],
        kegg_disease=row['kegg_disease'],
        disease=row['disease'],
        host_name=row['host_name'],
        host_lineage=row['host_lineage'],
        human_commensal=row['human_commensal'],
        antimicrobial_susceptibility=row['antimicrobial_susceptibility'],
        optimal_temperature=row['optimal_temperature'],
        extreme_environment=row['extreme_environment'],
        optimal_ph=row['optimal_ph'],
        animal_pathogen=row['animal_pathogen'],
        spore_forming=row['spore_forming'],
        pathogenicity=row['pathogenicity'],
        plant_pathogen=row['plant_pathogen'],
    ).save()


def save_euk(tree_node, row):
    Fungi(
        tree_node=tree_node,
        taxon_id=str(row['taxonomic_id']).strip(),
        salinity_concentration_range_w_v=row['salinity_concentration/range(w/v)'],
        gram_stain=row['gram_stain'],
        human_commensal=row['human_commensal'],
        antimicrobial_susceptibility=row['antimicrobial_susceptibility'],
        optimal_temperature=row['optimal_temperature'],
        extreme_environment=row['extreme_environment'],
        biofilm_forming=row['biofilm_forming'],
        optimal_ph=row['optimal_ph'],
        animal_pathogen=row['animal_pathogen'],
        spore_forming=row['spore_forming'],
        pathogenicity=row['pathogenicity'],
        plant_pathogen=row['plant_pathogen'],
        halotolerance=row['halotolerance'],
    ).save()


def save_archaea(tree_node, row):
    Archaea(
        tree_node=tree_node,
        taxon_id=str(row['taxonomic_id']).strip(),
        salinity_concentration_range_w_v=row['salinity_concentration_range_w_v'],
        low_ph=row['low_ph'],
        high_ph=row['high_ph'],
        drylands=row['drylands'],
        low_productivity=row['low_productivity'],
        gram_stain=row['gram_stain'],
        human_commensal=row['human_commensal'],
        antimicrobial_susceptibility=row['antimicrobial_susceptibility'],
        optimal_temperature=row['optimal_temperature'],
        extreme_environment=row['extreme_environment'],
        biofilm_forming=row['biofilm_forming'],
        optimal_ph=row['optimal_ph'],
        animal_pathogen=row['animal_pathogen'],
        spore_forming=row['spore_forming'],
        pathogenicity=row['pathogenicity'],
        plant_pathogen=row['plant_pathogen'],
        halotolerance=row['halotolerance'],
        psychrophilic=row['psychrophilic'],
        radiophilic=row['radiophilic'],
    ).save()


def save_bacteria(tree_node, row):
    Bacteria(
        tree_node=tree_node,
        taxon_id=str(row['taxonomic_id']).strip(),
        salinity_concentration_range_w_v=row['salinity_concentration_range_w_v'],
        low_ph=row['low_ph'],
        high_ph=row['high_ph'],
        drylands=row['drylands'],
        low_productivity=row['low_productivity'],
        gram_stain=row['gram_stain'],
        human_commensal=row['human_commensal'],
        antimicrobial_susceptibility=row['antimicrobial_susceptibility'],
        optimal_temperature=row['optimal_temperature'],
        extreme_environment=row['extreme_environment'],
        biofilm_forming=row['biofilm_forming'],
        optimal_ph=row['optimal_ph'],
        animal_pathogen=row['animal_pathogen'],
        spore_forming=row['spore_forming'],
        pathogenicity=row['pathogenicity'],
        plant_pathogen=row['plant_pathogen'],
        halotolerance=row['halotolerance'],
        psychrophilic=row['psychrophilic'],
        radiophilic=row['radiophilic'],
    ).save()


def populate_md2(limit=-1):
    for kind, tbl in [('virus', virus()), ('bact', bacteria()), ('euk', eukaryote())]:
        for i, (index, row) in enumerate(tbl.iterrows()):
            if limit > 0 and i >= limit:
                break
            taxon_id = str(row['taxonomic_id']).strip()

            try:
                tree_node = TreeNode.objects.get(taxon_id=taxon_id)
            except ObjectDoesNotExist:
                continue
            if kind == 'virus':
                save_virus(tree_node, row)
            elif kind == 'euk':
                save_euk(tree_node, row)
            elif kind == 'bact':
                ancestors = tree_node.ancestors(reducer=lambda x: x.canon_name.name.lower())
                if 'archaea' in ancestors:
                    save_archaea(tree_node, row)
                else:
                    save_bacteria(tree_node, row)

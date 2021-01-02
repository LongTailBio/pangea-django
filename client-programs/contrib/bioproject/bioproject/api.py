
from .bioproject import BioProject


def sra_files_from_bioproject(accession):
    bioproj = BioProject(accession)
    for sra_rec in bioproj.get_sra_records():
        for sra_file in sra_rec.get_sra_files():
            yield sra_file

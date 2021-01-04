
import json
import pandas as pd
import microbe_directory
from pangea_api import (
    Sample,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
    SampleGroup,
)

from ..base_module import Module
from ..data_utils import (
    sample_module_field,
)
from .constants import KRAKENUNIQ_NAMES
from .parse_utils import (
    parse_taxa_report,
    proportions,
    group_taxa_report,
)

COLS = {
    'gram_stain': lambda x: 'Gram Positive' if x else 'Gram Negative',
    'microbiome_location': lambda x: 'Human Commensal' if x else 'Not Human',
    'antimicrobial_susceptibility': lambda x: 'Known ABX' if x else 'No Known ABX',
    'optimal_temperature': lambda x: str(int(x)) + 'c',
    'extreme_environment': lambda x: 'Extremophile' if x else 'Mesophile',
    'biofilm_forming': lambda x: 'Forms Biofilms' if x else 'No Biofilms',
    'optimal_ph': lambda x: 'pH ' + str(x),
    'animal_pathogen': lambda x: 'Animal Pathogen' if x else 'Not an Animal Pathogen',
    'spore_forming': lambda x: 'Forms Spores' if x else 'No Spores',
    'pathogenicity': lambda x: 'Cogem ' + str(int(x)),
    'plant_pathogen': lambda x: 'Plant Pathogen' if x else 'Not a Plant Pathogen',
}


def process(samples, grp):
    taxa_matrix = 100 * group_taxa_report(grp)(samples)
    taxa_matrix.columns = [
        el.split('|')[-1].split('__')[1].replace('_', ' ') for el in taxa_matrix.columns
    ]
    MD1 = microbe_directory.md1()
    taxa = list(set(MD1.index) & set(taxa_matrix.columns))

    def process_sample(row):
        row = row[taxa]
        out = {}
        for property_name in MD1.columns:
            if property_name not in COLS:
                continue
            col = MD1.loc[taxa, property_name]
            annotated = row.groupby(col).sum()
            annotated.index = annotated.index.to_series().map(COLS[property_name])
            annotated['Unknown'] = 100 - annotated.sum()
            out[property_name] = annotated.to_dict()
        return out

    out = {}
    for sample_name, row in taxa_matrix.iterrows():
        out[sample_name] = process_sample(row)
    return out


class MicrobeDirectoryModule(Module):
    """TopTaxa AnalysisModule."""

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'microbe_directory'

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        samples = [
            sample for sample in grp.get_samples()
            if cls.sample_has_required_modules(sample)
        ]
        data = json.loads(json.dumps(process(samples, grp)))
        field = grp.analysis_result(
            cls.name(),
            replicate=cls.group_replicate(len(samples))
        ).field(
            'md1',
            data={'samples': data}
        )
        return field

    @classmethod
    def process_sample(cls, sample: Sample) -> SampleAnalysisResultField:
        data = json.loads(json.dumps(process([sample])))
        field = sample.analysis_result(
            cls.name(),
            replicate=cls.sample_replicate()
        ).field(
            'md1',
            data={'samples': data}
        )
        return field

    @classmethod
    def group_has_required_modules(cls, grp: SampleGroup) -> bool:
        for sample in grp.get_samples():
            if cls.sample_has_required_modules(sample):
                return True
        return False

    @classmethod
    def sample_has_required_modules(cls, sample: Sample) -> bool:
        """Return True iff this sample can be processed."""
        try:
            sample_module_field(sample, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1])
            return True
        except KeyError:
            return False

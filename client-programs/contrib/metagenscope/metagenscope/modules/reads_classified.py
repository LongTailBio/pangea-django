
import pandas as pd
import json
from pangea_api import (
    Sample,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
    SampleGroup,
)

from ..base_module import Module
from ..data_utils import (
    group_samples_by_metadata,
    sample_module_field,
)
from .constants import READS_CLASSIFIED_NAMES
from .parse_utils import parse_generic


def parse_sample(sample):
    data = parse_generic(
        sample_module_field(sample, READS_CLASSIFIED_NAMES[0], READS_CLASSIFIED_NAMES[1]),
        lambda x: json.loads(x.read())['proportions']
    )
    del data['total']
    return data


def sample_has_modules(sample):
    try:
        sample_module_field(sample, READS_CLASSIFIED_NAMES[0], READS_CLASSIFIED_NAMES[1])
        return True
    except KeyError:
        return False


class ReadsClassifiedModule(Module):
    """TopTaxa AnalysisModule."""
    MIN_SIZE = 3

    @classmethod
    def _name(cls):
        """Return unique id string."""
        return 'reads_classified'

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        samples = [
            sample for sample in grp.get_samples()
            if sample_has_modules(sample)
        ]
        field = grp.analysis_result(
            cls.name(),
            cls.group_replicate(len(samples))
        ).field(
            'json',
            data={
                'samples': {
                    sample.name: parse_sample(sample)
                    for sample in samples
                }
            },
        )
        return field

    @classmethod
    def group_has_required_modules(cls, grp: SampleGroup) -> bool:
        count = 0
        for sample in grp.get_samples():
            if sample_has_modules(sample):
                count += 1
            if count >= cls.MIN_SIZE:
                return True
        return False

    @classmethod
    def process_sample(cls, sample: Sample) -> SampleAnalysisResultField:
        field = sample.analysis_result(cls.name()).field(
            'json',
            data={'samples': {sample.name: parse_sample(sample)}}
        )
        return field

    @classmethod
    def sample_has_required_modules(cls, sample: Sample) -> bool:
        """Return True iff this sample can be processed."""
        return sample_has_modules(sample)

    @classmethod
    def process_sample(cls, sample: Sample) -> SampleAnalysisResultField:
        field = sample.analysis_result(
            cls.name(),
            cls.sample_replicate()
        ).field(
            'json',
            data={'samples': {sample.name: parse_sample(sample)}}
        )
        return field

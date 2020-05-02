"""AnalysisModule classes."""
from pangea_api import (
    Sample,
    SampleAnalysisResultField,
    SampleGroupAnalysisResultField,
    SampleGroup,
)

from .exceptions import UnsupportedAnalysisMode


class Module:

    @classmethod
    def name(cls) -> str:
        return f'metagenscope::v3.0.0::{cls._name()}'

    @classmethod
    def _name(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def group_has_required_modules(cls, grp: SampleGroup) -> bool:
        """Return True iff the group can be processed.

        By default just checks that every sample has correct modules
        but can and should be overwritten.
        """
        for sample in grp.get_samples():
            if not cls.sample_has_required_modules(sample):
                return False
        return True

    @classmethod
    def sample_has_required_modules(cls, sample: Sample) -> bool:
        """Return True iff this sample can be processed."""
        raise NotImplementedError()

    @classmethod
    def process_sample(cls, sample: Sample) -> SampleAnalysisResultField:
        """Return an analysis result containing processed data.

        Assume sample has required modules.
        """
        raise UnsupportedAnalysisMode()

    @classmethod
    def process_group(cls, grp: SampleGroup) -> SampleGroupAnalysisResultField:
        """Return an analysis result containing processed data.

        Assume group has required modules.
        """
        raise UnsupportedAnalysisMode()

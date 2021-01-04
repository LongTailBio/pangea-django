from .autometa import (
    add_taxa_auto_metadata,
    regularize_metadata,
)
from .modules import (
    TopTaxaModule,
    SampleSimilarityModule,
    AveGenomeSizeModule,
    AlphaDiversityModule,
    MultiAxisModule,
    VolcanoModule,
    MicrobeDirectoryModule,
    TaxaSunburstModule,
    ReadsClassifiedModule,
    CovidFastDetectModule,
)
from .version import VERSION, compare_versions
import logging

GROUP_MODULES = [
    ReadsClassifiedModule,
    MultiAxisModule,
    AlphaDiversityModule,
    TopTaxaModule,
    AveGenomeSizeModule,
    SampleSimilarityModule,
    VolcanoModule,
    MicrobeDirectoryModule,
    CovidFastDetectModule,
]

SAMPLE_MODULES = [
    MicrobeDirectoryModule,
    ReadsClassifiedModule,
    TaxaSunburstModule,
]

logger = logging.getLogger(__name__)


def auto_metadata(samples, grp):
    regularize_metadata(samples)
    add_taxa_auto_metadata(samples, grp)


def module_should_be_rerun(module, analysis_result, samples):
    try:
        version, timetamp, n_samples = analysis_result.replicate.split('-')
        timetamp = int(timetamp)
        n_samples = int(n_samples)
    except ValueError:
        return True
    if compare_versions(VERSION, version) > 0:
        return True
    new_n_samples = 0
    for sample in samples:
        if module.sample_has_required_modules(sample):
            new_n_samples += 1
    if new_n_samples > n_samples:
        return True
    return False


def run_group(grp, strict=False):
    already_run = {ar.module_name: ar for ar in grp.get_analysis_results()}
    samples = list(grp.get_samples())
    for module in GROUP_MODULES:
        if module.name() in already_run and not module_should_be_rerun(module, already_run[module.name()], samples):
            logger.info(f'Module {module.name()} has already been run for this group')
            continue
        if not module.group_has_required_modules(grp):
            logger.info(f'Group does not meet requirements for module {module.name()}')
            continue
        logger.info(f'Group meets requirements for module {module.name()}, processing')
        try:
            field = module.process_group(grp)
        except Exception as e:
            logger.warning(f'failed while running module {module.name()} for group {grp.name}\nException:\n{e}')
            if strict:
                raise
        try:
            field.idem()
            logger.info('saved.')
        except Exception as e:
            logger.warning(f'failed while saving module {module.name()} for group {grp.name}\nException:\n{e}')
            if strict:
                raise
    logger.info(f'finished processing modules for group {grp.name}.')


def run_sample(sample, strict=False):
    already_run = {ar.module_name for ar in sample.get_analysis_results()}
    for module in SAMPLE_MODULES:
        if module.name() in already_run:
            logger.info(f'Module {module.name()} has already been run for this sample')
            continue
        if not module.sample_has_required_modules(sample):
            logger.info(f'Sample does not meet requirements for module {module.name()}')
            continue
        logger.info(f'Sample meets requirements for module {module.name()}, processing')
        try:
            field = module.process_sample(sample)
            logger.info('done.')
        except Exception as e:
            logger.warning(f'failed while running module {module.name()} for sample {sample.name}\nException:\n{e}')
            if strict:
                raise
        try:
            field.idem()
            logger.info('saved.')
        except Exception as e:
            logger.warning(f'failed while saving module {module.name()} for sample {sample.name}\nException:\n{e}')
            if strict:
                raise
    logger.info(f'finished processing modules for sample {sample.name}.')

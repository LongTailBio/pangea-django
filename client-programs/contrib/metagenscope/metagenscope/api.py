from .autometa import add_taxa_auto_metadata
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
)

GROUP_MODULES = [
    ReadsClassifiedModule,
    MultiAxisModule,
    AlphaDiversityModule,
    TopTaxaModule,
    AveGenomeSizeModule,
    SampleSimilarityModule,
    VolcanoModule,
    MicrobeDirectoryModule,
]

SAMPLE_MODULES = [
    MicrobeDirectoryModule,
    ReadsClassifiedModule,
    TaxaSunburstModule,
]


def auto_metadata(samples, logger):
    add_taxa_auto_metadata(samples, logger)


def run_group(grp, logger):
    already_run = {ar.module_name for ar in grp.get_analysis_results()}
    for module in GROUP_MODULES:
        if module.name() in already_run:
            logger(f'Module {module.name()} has already been run for this group')
            continue
        if not module.group_has_required_modules(grp):
            logger(f'Group does not meet requirements for module {module.name()}')
            continue
        logger(f'Group meets requirements for module {module.name()}, processing')
        field = module.process_group(grp)
        field.idem()
        logger('done.')


def run_sample(sample, logger):
    already_run = {ar.module_name for ar in sample.get_analysis_results()}
    for module in SAMPLE_MODULES:
        if module.name() in already_run:
            logger(f'Module {module.name()} has already been run for this sample')
            continue
        if not module.sample_has_required_modules(sample):
            logger(f'Sample does not meet requirements for module {module.name()}')
            continue
        logger(f'Sample meets requirements for module {module.name()}, processing')
        field = module.process_sample(sample)
        field.idem()
        logger('done.')

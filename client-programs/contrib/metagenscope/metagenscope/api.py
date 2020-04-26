
import pandas as pd
from .modules.constants import KRAKENUNIQ_NAMES
from .modules.parse_utils import(
    proportions,
    run_pca,
    parse_taxa_report,
)
from .data_utils import sample_module_field


def sample_has_modules(sample):
    has_all = True
    for module_name, field, _ in [KRAKENUNIQ_NAMES]:
        try:
            sample_module_field(sample, module_name, field)
        except KeyError:
            has_all = False
    return has_all


def auto_metadata(samples):
    taxa_matrix = proportions(pd.DataFrame.from_dict(
        {
            sample.name: parse_taxa_report(
                sample_module_field(sample, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1])
            )
            for sample in samples
            if sample_has_modules(sample)
        },
        orient='index'
    ).fillna(0))
    pc1 = run_pca(taxa_matrix, n_comp=1)['C0']
    for sample in samples:
        pcval = 'Not Found in PC1'
        if pc1[sample.name] >= pc1.median():
            pcval = 'Above PC1 Median'
        elif pc1[sample.name] < pc1.median():
            pcval = 'Below PC1 Median'
        sample.metadata['MGS - PC1'] = pcval

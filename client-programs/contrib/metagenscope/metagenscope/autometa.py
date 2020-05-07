
import pandas as pd
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype
from sklearn.cluster import dbscan
from .modules.constants import KRAKENUNIQ_NAMES
from .modules.parse_utils import (
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


def pc1_median(samples, taxa_matrix):
    pc1 = run_pca(taxa_matrix, n_comp=1)['C0']
    for sample in samples:
        pcval = 'Not Found in PC1'
        if pc1[sample.name] >= pc1.median():
            pcval = 'Above PC1 Median'
        elif pc1[sample.name] < pc1.median():
            pcval = 'Below PC1 Median'
        sample.metadata['MGS - PC1'] = pcval


def pca_dbscan(samples, taxa_matrix):
    pca = run_pca(taxa_matrix, n_comp=min(10, taxa_matrix.shape[1]))
    _, cluster_labels = dbscan(pca, eps=0.1, min_samples=3)
    for i, sample in enumerate(samples):
        label_val = cluster_labels[i]
        label = f'Cluster {label_val}'
        if label_val < 0:
            label = f'Noise'
        sample.metadata['MGS - PCA-DBSCAN'] = label


def add_taxa_auto_metadata(samples, logger):
    samples = [sample for sample in samples if sample_has_modules(sample)]
    taxa_matrix = proportions(pd.DataFrame.from_dict(
        {
            sample.name: parse_taxa_report(
                sample_module_field(sample, KRAKENUNIQ_NAMES[0], KRAKENUNIQ_NAMES[1])
            )
            for sample in samples
        },
        orient='index'
    ).fillna(0))
    logger('Adding PCA median variable...')
    pc1_median(samples, taxa_matrix)
    logger('done.')
    logger('Adding PCA DBSCAN variable...')
    pca_dbscan(samples, taxa_matrix)
    logger('done.')


def regularize_metadata(samples, logger):
    logger('Regularizing metadata...')
    meta = pd.DataFrame.from_dict(
        {sample.name: sample.metadata for sample in samples},
        orient='index'
    )

    def regularize_numeric(col):
        try:
            col = pd.qcut(col, 3, labels=["low", "medium", "high"], duplicates='drop')
        except ValueError:
            pass
        col = col.astype(str)
        col = col.map(lambda x: 'Unknown' if x.lower() == 'nan' else x)
        col = col.fillna('Unknown')
        return col

    def regularize_categorical(col):
        col = col.fillna('Unknown')
        min_size = max(2, col.shape[0] // 100)
        counts = col.value_counts()
        others = list(counts[counts < min_size].index)
        col = col.map(lambda el: 'Other' if el in others else el)
        return col

    def regularize_col(col):
        if is_numeric_dtype(col):
            return regularize_numeric(col)
        if is_string_dtype(col):
            return regularize_categorical(col)
        return col

    meta = meta.apply(regularize_col, axis=0)
    meta = meta.fillna('Unknown')
    for sample in samples:
        try:
            sample.metadata = meta.loc[sample.name].to_dict()
        except KeyError:
            pass
    logger('done.')

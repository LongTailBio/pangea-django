
import pandas as pd
import logging
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype
from sklearn.cluster import dbscan
from .modules.constants import KRAKEN2_NAMES
from .modules.parse_utils import (
    proportions,
    run_pca,
    parse_taxa_report,
    group_taxa_report,
)
from .data_utils import sample_module_field

logger = logging.getLogger(__name__)


def sample_has_modules(sample):
    has_all = True
    for module_name, field, _ in [KRAKEN2_NAMES]:
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


def add_taxa_auto_metadata(samples, grp):
    samples = [sample for sample in samples if sample_has_modules(sample)]
    taxa_matrix = group_taxa_report(grp)(samples)
    parsed_sample_names = set(taxa_matrix.index.to_list())
    samples = [sample for sample in samples if sample.name in parsed_sample_names]
    logger.info('Adding PCA median variable...')
    pc1_median(samples, taxa_matrix)
    logger.info('done.')
    logger.info('Adding PCA DBSCAN variable...')
    pca_dbscan(samples, taxa_matrix)
    logger.info('done.')


def regularize_metadata(samples):
    logger.info('Regularizing metadata...')
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
    logger.info('done.')

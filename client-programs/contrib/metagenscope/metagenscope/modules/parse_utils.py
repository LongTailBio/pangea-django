import os
import pandas as pd
import numpy as np
from umap import UMAP
from ..remote_utils import download_s3_file
from pangea_api import (
    SampleAnalysisResultField,
)
from sklearn.decomposition import PCA


def format_taxon_name(taxon):
    taxon = taxon.replace('_', ' ')
    taxon = taxon[0].upper() + taxon[1:].lower()
    return taxon


def proportions(tbl):
    tbl = (tbl.T / tbl.T.sum()).T
    return tbl


def parse_generic(report: SampleAnalysisResultField, parser):
    local_path = report.download_file()
    with open(local_path) as taxa_file:
        out = parser(taxa_file)
    return out


def group_taxa_report(pangea_group, module_name='cap2::capalyzer::kraken2_taxa', field_name='read_counts'):
    """Return a function that will return a pandas data frame with taxa abundances."""
    field = pangea_group.analysis_result(module_name).field(field_name).get()
    filename = field.download_file()
    taxa_tbl = pd.read_csv(filename, index_col=0)
    sample_names = set(taxa_tbl.index.to_list())

    def taxa_report(samples, as_proportions=True):
        """Return a dataframe with taxon abundances for the samples."""
        my_sample_names = [sample.name for sample in samples if sample.name in sample_names]
        my_taxa = taxa_tbl.loc[my_sample_names]
        my_taxa = my_taxa.fillna(0)
        if as_proportions:
            my_taxa = proportions(my_taxa)
        return my_taxa

    return taxa_report


def parse_taxa_report(report: SampleAnalysisResultField, proportions=True) -> dict:
    """Return a dict of taxa_name to relative abundance."""
    local_path = report.download_file()
    out, abundance_sum = {}, 0
    with open(local_path) as taxa_file:
        for line_num, line in enumerate(taxa_file):
            line = line.strip()
            tkns = line.split('\t')
            if not line or len(tkns) < 2:
                continue
            if len(tkns) == 2:
                out[tkns[0]] = float(tkns[1])
                abundance_sum += float(tkns[1])
            else:
                if line_num == 0:
                    continue
                out[tkns[1]] = float(tkns[3])
                abundance_sum += float(tkns[3])
    if proportions:
        out = {k: v / abundance_sum for k, v in out.items()}
    return out


def umap(mytbl, **kwargs):
    """Retrun a Pandas dataframe with UMAP, make a few basic default decisions."""
    metric = 'jaccard'
    if mytbl.shape[0] == mytbl.shape[1]:
        metric = 'precomputed'
    n_comp = kwargs.get('n_components', 2)
    umap_tbl = pd.DataFrame(UMAP(
        n_neighbors=kwargs.get('n_neighbors', min(100, int(mytbl.shape[0] / 4))),
        n_components=n_comp,
        metric=kwargs.get('metric', metric),
        random_state=kwargs.get('random_state', 42)
    ).fit_transform(mytbl))
    umap_tbl.index = mytbl.index
    umap_tbl = umap_tbl.rename(columns={i: f'C{i}' for i in range(n_comp)})
    return umap_tbl


def run_pca(tbl, n_comp=2):
    tbl = proportions(tbl)
    pca = PCA(n_components=n_comp)
    tbl_pca = pd.DataFrame(pca.fit_transform(tbl))
    tbl_pca.index = tbl.index
    tbl_pca = tbl_pca.rename(columns={i: f'C{i}' for i in range(n_comp)})
    return tbl_pca

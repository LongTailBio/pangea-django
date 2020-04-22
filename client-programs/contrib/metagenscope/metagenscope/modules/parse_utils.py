import os
import pandas as pd
import numpy as np
from umap import UMAP
from ..remote_utils import download_s3_file
from pangea_api import (
    SampleAnalysisResultField,
)


def proportions(tbl):
    tbl = (tbl.T / tbl.T.sum()).T
    return tbl


def parse_taxa_report(report: SampleAnalysisResultField) -> dict:
    """Return a dict of taxa_name to relative abundance."""
    blob = report.stored_data
    local_path = download_s3_file(blob)
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
    os.remove(local_path)
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

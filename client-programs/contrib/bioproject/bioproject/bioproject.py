
from Bio import Entrez
import xml.etree.ElementTree as ET
import pandas as pd
import json
import time


class BioProject:

    def __init__(self, accession):
        self.accession = accession
        self._sra_records = None

    def get_sra_ids(self):
        handle = Entrez.esearch(db="sra", term=self.accession)
        record = Entrez.read(handle)
        handle.close()
        return record['IdList']

    def get_sra_records(self):
        if self._sra_records:
            return self._sra_records
        self._sra_records = [SRARecord(self, sra_id) for sra_id in self.get_sra_ids()]
        return self._sra_records

    def __str__(self):
        return f'<BioProject accession={self.accession} />'

    def to_table(self, sleep=5):
        rows = []
        for sra_rec in self.get_sra_records():
            time.sleep(sleep)
            for sra_file in sra_rec.get_sra_files():
                kind = sra_file.blob['semantic_name']
                kind = 'sra_run' if kind == 'run' else kind
                if kind == 'fastq':
                    try:
                        fname = sra_file.blob['filename']
                    except KeyError:
                        continue
                    for ext in ['_{}.f', '_R{}.f', '_read{}.f', '_r{}.f', '.{}.f']:
                        for end in [1, 2]:
                            if ext.format(end) in fname:
                                kind = f'read_{end}'
                    kind = 'unpaired_read' if kind == 'fastq' else kind
                assert kind in ['sra_run', 'read_1', 'read_2', 'unpaired_read'], f'kind is {kind}, {sra_file.blob}'
                rows.append({
                    'bioproject': self.accession,
                    'sra_rec': sra_rec.accession,
                    'sra_file_kind': kind,
                    'sra_file_blob': json.dumps(sra_file.blob)
                })
        tbl = pd.DataFrame(rows)
        return tbl


class SRARecord:

    def __init__(self, bioproject, accession):
        self.bioproject = bioproject
        self.accession = accession
        self.root = None
        self.sra_files = []

    def fetch(self):
        if self.root:
            return self
        handle = Entrez.efetch(db='sra', id=self.accession)
        xml_str = handle.read()
        self.root = ET.fromstring(xml_str)
        return self

    def get_sra_files(self):
        if self.sra_files:
            return self.sra_files
        self.sra_files = self._get_sra_files()
        return self.get_sra_files()

    def _get_sra_files(self, root=None):
        if root is None:
            root = self.fetch().root
        sra_files = root.findall('SRAFile')
        sra_files = [SRAFile(self, xml_rec) for xml_rec in sra_files]
        for child in root:
            sra_files += self._get_sra_files(root=child)
        return sra_files

    def get_sample_accession(self):
        root = self.fetch().root
        sample = root.findall('EXPERIMENT_PACKAGE')[0].findall('SAMPLE')[0]
        return sample.attrib['accession']

    def __str__(self):
        return f'<SRARecord accession={self.accession} bioproject={self.bioproject.accession}/>'


class SRAFile:

    def __init__(self, sra_rec, xml):
        self.sra_rec = sra_rec
        self.xml = xml
        self.blob = xml.attrib

    def __str__(self):
        return f'<SRAFile tag={self.xml.tag} srarecord={self.sra_rec.accession} filename={self.blob["filename"]} />'

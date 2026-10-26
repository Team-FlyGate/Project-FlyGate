"""tests/fixtures/omics_fixture.json.gz 를 만듭니다. 자리 표시 값과 실제 조회값의 구분은 같은 폴더의 README 에 있습니다.

사용: python3 tests/fixtures/make_omics_fixture.py tests/fixtures/omics_fixture.json.gz
"""
import gzip, json, sys

DRD2_TISSUES = ["UBERON_0001008", "UBERON_0001017", "UBERON_0004535", "UBERON_0005409"]
x = {
    "asof": "2026-10-26",
    "versions": {"tooluniverse": "1.5.7", "opentargets": "25.09", "gtex": "gtex_v10",
                 "ols_efo": "placeholder", "hpo": "placeholder", "mondo": "placeholder"},
    "gtex_tissues": {"Whole_Blood": "Blood", "Liver": "Liver", "Brain_Cortex": "Brain"},
    "drugs": {
        "NIRAPARIB": {"chembl_id": "CHEMBL1094636", "match": "name_exact",
                      "targets": ["ENSG00000143799", "ENSG00000129484"]},
        "CLOZAPINE": {"chembl_id": "placeholder", "match": "name_exact", "targets": ["ENSG00000149295"]},
    },
    "targets": {
        "ENSG00000143799": {"symbol": "PARP1",
                            "moa": [{"drug": "NIRAPARIB", "action": "INHIBITOR",
                                     "mechanism": "Poly [ADP-ribose] polymerase-1 inhibitor", "dgidb": True}],
                            "safety": None,
                            "gtex": {"Whole_Blood": 8.5, "Liver": 4.25, "Brain_Cortex": 6.0}},
        "ENSG00000129484": {"symbol": "PARP2",
                            "moa": [{"drug": "NIRAPARIB", "action": "placeholder", "mechanism": "placeholder",
                                     "dgidb": None}],
                            "safety": None,
                            "gtex": {"Whole_Blood": 3.5, "Liver": 2.0, "Brain_Cortex": 1.5}},
        "ENSG00000149295": {"symbol": "DRD2",
                            "moa": [{"drug": "CLOZAPINE", "action": "placeholder", "mechanism": "placeholder",
                                     "dgidb": None}],
                            "safety": [{"event": "catalepsy", "event_id": "EFO_0009845", "tissue_ids": DRD2_TISSUES,
                                        "datasource": "Lynch et al. (2017)", "pmid": "28216264"},
                                       {"event": "placeholder liability", "event_id": None, "tissue_ids": [],
                                        "datasource": "placeholder", "pmid": None}],
                            "gtex": {"Whole_Blood": 0.25, "Liver": 0.5, "Brain_Cortex": 2.75}},
    },
    "terms": {
        "thrombocytopenia": {"id": "HP_0001873", "label": "Thrombocytopenia", "match": "label", "source": "ols_efo",
                             "ancestors": ["HP_0011875", "HP_0001871", "HP_0000118", "EFO_0000651"],
                             "organs": {"sites": ["Blood"], "method": "hpo_ancestor_label",
                                        "evidence": [{"ancestor": "HP_0001871", "word": "blood"}]}},
        "catalepsy": {"id": "EFO_0009845", "label": "catalepsy", "match": "label", "source": "ols_efo",
                      "ancestors": [], "organs": None},
        "some unmapped term": {"id": None, "label": None, "match": "none", "source": None,
                               "ancestors": None, "organs": None},
    },
    "pairs": {
        "NIRAPARIB|thrombocytopenia": {"term": "thrombocytopenia", "safety_match": [],
                                       "assoc": {"score": 0.0125, "score_no_literature": 0.0, "row_found": True}},
        "CLOZAPINE|catalepsy": {"term": "catalepsy",
                                "safety_match": [{"target": "ENSG00000149295", "index": 0, "relation": "term"}],
                                "assoc": {"score": None, "score_no_literature": None, "row_found": False}},
        "CLOZAPINE|some unmapped term": {"term": "some unmapped term", "safety_match": None, "assoc": None},
    },
    "errors": [],
}
with open(sys.argv[1], "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as f:
    f.write(json.dumps(x, ensure_ascii=False, separators=(",", ":")).encode())

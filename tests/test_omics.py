"""오믹스 근거 층(L1-L4)을 작은 추출 파일로 네트워크 없이 검사합니다.

tests/fixtures/omics_fixture.json.gz 는 두 약물(니라파립, 클로자핀)과 세 쌍을 담습니다. 상한(5개)과 복합제 키는
테스트 안에서 만든 합성 추출로 봅니다. 자리 표시 값은 tests/fixtures/README.md 에 적었습니다.
"""
import gzip
import json
import pathlib
import shutil

import pytest

from _fv import omics

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "omics_fixture.json.gz"
TAIL = "Population-level mechanistic context; not evidence that the drug caused this reaction in this case."


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    shutil.copy(FIXTURE, tmp_path / "omics.json.gz")
    monkeypatch.setattr(omics, "DATA", tmp_path)
    omics._omics.cache_clear()
    yield tmp_path
    omics._omics.cache_clear()


def write(path, extract):
    with gzip.open(path / "omics.json.gz", "wt") as f:
        json.dump(extract, f)
    omics._omics.cache_clear()


# ---------------------------------------------------------------- 추출 파일과 적재
def test_fixture_is_gzipped_extract_loaded_through_cache():
    with gzip.open(FIXTURE, "rt") as f:
        assert set(json.load(f)) == {"asof", "versions", "gtex_tissues", "drugs", "targets", "terms", "pairs", "errors"}
    assert omics.drugs() == ["CLOZAPINE", "NIRAPARIB"]


def test_missing_file_gives_empty_structure(data):
    (data / "omics.json.gz").unlink()
    omics._omics.cache_clear()
    assert omics.drugs() == []
    assert omics.pair("NIRAPARIB", "thrombocytopenia") is None
    assert omics.drug_pairs("NIRAPARIB") is None
    shutil.copy(FIXTURE, data / "omics.json.gz")
    omics._omics.cache_clear()
    assert omics.pair("NIRAPARIB", "thrombocytopenia")["term"] == "thrombocytopenia"


# ---------------------------------------------------------------- 쌍 찾기
def test_pair_normalizes_case_only():
    assert omics.pair("Niraparib", "THROMBOCYTOPENIA") == {
        "drug": "NIRAPARIB", "pt": "thrombocytopenia", "term": "thrombocytopenia", "mapping": "label",
        "safety_match": [], "assoc": {"score": 0.0125, "score_no_literature": 0.0, "row_found": True},
        "safety_recorded": False}
    assert omics.pair("NIRAPARIB", " thrombocytopenia") is None
    assert omics.pair("OLAPARIB", "thrombocytopenia") is None
    assert omics.pair("NIRAPARIB", "anaemia") is None


def test_drug_pairs_lists_every_pair_of_a_drug():
    assert [(p["pt"], p["mapping"], p["safety_recorded"]) for p in omics.drug_pairs("clozapine")] == [
        ("catalepsy", "label", True), ("some unmapped term", "none", True)]
    assert omics.drug_pairs("OLAPARIB") is None


# ---------------------------------------------------------------- 근거 항목 (L1-L4)
def item(id, layer, what, n, **extra):
    return {"id": id, "layer": layer, "what": f"{what} {TAIL}", "n": n, **extra}


PARP1 = item("omics:target:NIRAPARIB:PARP1@OT25.09", "L1",
             "PARP1 (ENSG00000143799) is a mechanism-of-action target of NIRAPARIB in Open Targets: INHIBITOR, "
             "Poly [ADP-ribose] polymerase-1 inhibitor. Open Targets records no safety liability field for PARP1 "
             "(nothing recorded, not zero).", {"liabilities": None})
DRD2 = item("omics:target:CLOZAPINE:DRD2@OT25.09", "L1",
            "DRD2 (ENSG00000149295) is a mechanism-of-action target of CLOZAPINE in Open Targets: placeholder, "
            "placeholder. Open Targets lists 2 safety liabilities for DRD2.", {"liabilities": 2})
CATALEPSY_WHAT = ("Open Targets safety liability of DRD2: catalepsy (EFO_0009845); tissues UBERON_0001008, "
                  "UBERON_0001017, UBERON_0004535, UBERON_0005409; source Lynch et al. (2017), PMID 28216264.")
NO_ID_WHAT = ("Open Targets safety liability of DRD2: placeholder liability (no event ID); tissues not recorded; "
              "source placeholder, PMID not recorded.")
DRD2_TOP = [
    item("omics:gtex:DRD2:Brain_Cortex@gtex_v10", "L3", "GTEx (gtex_v10) median expression of DRD2 in Brain_Cortex "
         "(tissue group Brain): 2.75 TPM, rank 1 of 3 tissues.", {"median_tpm": 2.75, "rank_of_54": 1}),
    item("omics:gtex:DRD2:Liver@gtex_v10", "L3", "GTEx (gtex_v10) median expression of DRD2 in Liver "
         "(tissue group Liver): 0.5 TPM, rank 2 of 3 tissues.", {"median_tpm": 0.5, "rank_of_54": 2}),
    item("omics:gtex:DRD2:Whole_Blood@gtex_v10", "L3", "GTEx (gtex_v10) median expression of DRD2 in Whole_Blood "
         "(tissue group Blood): 0.25 TPM, rank 3 of 3 tissues.", {"median_tpm": 0.25, "rank_of_54": 3}),
]


def test_items_honest_negative_niraparib():
    assert omics.items(omics.pair("NIRAPARIB", "thrombocytopenia")) == [
        PARP1,
        item("omics:target:NIRAPARIB:PARP2@OT25.09", "L1",
             "PARP2 (ENSG00000129484) is a mechanism-of-action target of NIRAPARIB in Open Targets: placeholder, "
             "placeholder. Open Targets records no safety liability field for PARP2 (nothing recorded, not zero).",
             {"liabilities": None}),
        item("omics:gtex:PARP1:Whole_Blood@gtex_v10", "L3", "GTEx (gtex_v10) median expression of PARP1 in "
             "Whole_Blood (tissue group Blood): 8.5 TPM, rank 1 of 3 tissues.", {"median_tpm": 8.5, "rank_of_54": 1}),
        item("omics:gtex:PARP2:Whole_Blood@gtex_v10", "L3", "GTEx (gtex_v10) median expression of PARP2 in "
             "Whole_Blood (tissue group Blood): 3.5 TPM, rank 1 of 3 tissues.", {"median_tpm": 3.5, "rank_of_54": 1}),
        item("omics:assoc:NIRAPARIB:HP_0001873@OT25.09", "L4",
             "Open Targets association between the targets of NIRAPARIB and HP_0001873 (Thrombocytopenia): "
             "score 0.0125, score without literature 0.0; literature co-mention only.",
             {"score": 0.0125, "score_no_literature": 0.0}),
    ]


def test_items_matched_liability_clozapine():
    assert omics.items(omics.pair("CLOZAPINE", "catalepsy")) == [
        DRD2,
        item("omics:safety:DRD2:EFO_0009845@OT25.09", "L2", CATALEPSY_WHAT, None, match="term"),
        item("omics:safety:DRD2:placeholder-liability@OT25.09", "L2", NO_ID_WHAT, None, match="none"),
        *DRD2_TOP,
        item("omics:assoc:CLOZAPINE:EFO_0009845@OT25.09", "L4",
             "Open Targets has no association row between the targets of CLOZAPINE and EFO_0009845 (catalepsy); "
             "nothing recorded, not a zero score.", {"score": None, "score_no_literature": None}),
    ]


def test_unmapped_term_has_no_l4_and_unmatched_l2():
    assert omics.items(omics.pair("CLOZAPINE", "some unmapped term")) == [
        DRD2,
        item("omics:safety:DRD2:EFO_0009845@OT25.09", "L2", CATALEPSY_WHAT, None, match="none"),
        item("omics:safety:DRD2:placeholder-liability@OT25.09", "L2", NO_ID_WHAT, None, match="none"),
        *DRD2_TOP,
    ]


def test_absent_safety_is_nothing_recorded_not_empty():
    negative, positive = omics.pair("NIRAPARIB", "thrombocytopenia"), omics.pair("CLOZAPINE", "catalepsy")
    assert (negative["safety_recorded"], positive["safety_recorded"]) == (False, True)
    assert [i["layer"] for i in omics.items(negative)] == ["L1", "L1", "L3", "L3", "L4"]
    assert [i["n"] for i in omics.items(negative) if i["layer"] == "L1"] == [{"liabilities": None}] * 2


def test_empty_safety_list_is_recorded_as_none_found(data):
    x = synthetic()
    x["targets"]["ENSG_TEST1"]["safety"] = []
    write(data, x)
    p = omics.pair("DRUGA\\DRUGB", "reaction x")
    assert p["safety_recorded"] is True
    assert [i["n"] for i in omics.items(p) if i["layer"] == "L1"] == [{"liabilities": 0}] * 7


def test_every_what_ends_with_tail_and_is_stable_per_id():
    seen, total = {}, 0
    for d in omics.drugs():
        for p in omics.drug_pairs(d):
            for i in omics.items(p):
                total += 1
                assert i["what"].endswith(" " + TAIL) and i["what"].count(TAIL) == 1
                assert seen.setdefault(i["id"], i["what"]) == i["what"]
    assert (total, len(seen)) == (18, 12)


# ---------------------------------------------------------------- 메모 상한 (합성 추출)
def synthetic():
    genes = {f"ENSG_TEST{k}": {"symbol": f"GENE{k}", "moa": [{"drug": "DRUGA\\DRUGB", "action": "A", "mechanism": "M"}],
                               "safety": [], "gtex": {"X1": float(k), "X2": k + 0.5, "Y1": 10.0 + k, "Y2": 20.0 + k,
                                                      "Y3": 30.0 + k, "Y4": 40.0 + k, "Y5": 50.0 + k}}
             for k in range(1, 8)}
    genes["ENSG_TEST1"]["safety"] = [
        {"event": "event a", "event_id": "TERM_ANC", "tissue_ids": [], "datasource": "s", "pmid": None},
        {"event": "event b", "event_id": "TERM_OTHER", "tissue_ids": [], "datasource": "s", "pmid": None}]
    return {"asof": "t", "versions": {"opentargets": "1.0", "gtex": "gtex_v10"},
            "gtex_tissues": {"X1": "Gx", "X2": "Gx", "Y1": "Gy", "Y2": "Gy", "Y3": "Gy", "Y4": "Gy", "Y5": "Gy"},
            "drugs": {"DRUGA\\DRUGB": {"targets": list(genes)}}, "targets": genes,
            "terms": {"reaction x": {"id": "TERM_X", "label": "reaction x", "match": "synonym", "ancestors": ["TERM_ANC"],
                                     "organs": {"sites": ["Gx"]}}},
            "pairs": {"DRUGA\\DRUGB|reaction x": {"term": "reaction x", "safety_match": [
                          {"target": "ENSG_TEST1", "index": 0, "relation": "ancestor"}],
                          "assoc": {"score": 0.5, "score_no_literature": 0.2, "row_found": True}},
                      "DRUGA\\DRUGB|reaction y": {"term": None, "safety_match": None,
                                                   "assoc": {"score": 0.5, "score_no_literature": 0.2, "row_found": True}}},
            "errors": []}


def test_combination_key_keeps_backslash(data):
    write(data, synthetic())
    assert omics.drugs() == ["DRUGA\\DRUGB"]
    p = omics.pair("druga\\drugb", "Reaction X")
    assert (p["drug"], p["pt"], p["mapping"]) == ("DRUGA\\DRUGB", "reaction x", "synonym")
    assert omics.pair("DRUGA+DRUGB", "reaction x") is None
    its = omics.items(p)
    assert (its[0]["id"], its[-1]["id"]) == ("omics:target:DRUGA+DRUGB:GENE1@OT1.0", "omics:assoc:DRUGA+DRUGB:TERM_X@OT1.0")


def test_memo_caps_targets_and_tissues_and_keeps_matched_liabilities(data):
    write(data, synthetic())
    p = omics.pair("DRUGA\\DRUGB", "reaction x")
    assert [(i["layer"], i.get("match")) for i in omics.items(p)][:10] == [("L1", None)] * 7 + [
        ("L2", "ancestor"), ("L2", "none"), ("L3", None)]
    assert len([i for i in omics.items(p) if i["layer"] == "L3"]) == 14
    assert [i["id"] for i in omics.items_for_memo(p)] == [
        "omics:target:DRUGA+DRUGB:GENE1@OT1.0", "omics:target:DRUGA+DRUGB:GENE2@OT1.0",
        "omics:target:DRUGA+DRUGB:GENE3@OT1.0", "omics:target:DRUGA+DRUGB:GENE4@OT1.0",
        "omics:target:DRUGA+DRUGB:GENE5@OT1.0",
        "omics:safety:GENE1:TERM_ANC@OT1.0",
        "omics:gtex:GENE7:X2@gtex_v10", "omics:gtex:GENE7:X1@gtex_v10", "omics:gtex:GENE6:X2@gtex_v10",
        "omics:gtex:GENE6:X1@gtex_v10", "omics:gtex:GENE5:X2@gtex_v10",
        "omics:assoc:DRUGA+DRUGB:TERM_X@OT1.0"]


def test_term_missing_from_pair_is_unmapped_with_top5_tissues(data):
    write(data, synthetic())
    p = omics.pair("DRUGA\\DRUGB", "reaction y")
    its = omics.items(p)
    assert p["mapping"] == "none" and [i["layer"] for i in its].count("L4") == 0
    assert [i["match"] for i in its if i["layer"] == "L2"] == ["none", "none"]
    assert [(i["id"], i["n"]) for i in its if i["id"].startswith("omics:gtex:GENE1:")] == [
        ("omics:gtex:GENE1:Y5@gtex_v10", {"median_tpm": 51.0, "rank_of_54": 1}),
        ("omics:gtex:GENE1:Y4@gtex_v10", {"median_tpm": 41.0, "rank_of_54": 2}),
        ("omics:gtex:GENE1:Y3@gtex_v10", {"median_tpm": 31.0, "rank_of_54": 3}),
        ("omics:gtex:GENE1:Y2@gtex_v10", {"median_tpm": 21.0, "rank_of_54": 4}),
        ("omics:gtex:GENE1:Y1@gtex_v10", {"median_tpm": 11.0, "rank_of_54": 5})]
    assert [i["layer"] for i in omics.items_for_memo(p)] == ["L1"] * 5


def test_literature_flag_only_when_no_literature_score_is_zero(data):
    lit = omics.items(omics.pair("NIRAPARIB", "thrombocytopenia"))[-1]["what"]
    write(data, synthetic())
    mixed = omics.items(omics.pair("DRUGA\\DRUGB", "reaction x"))[-1]["what"]
    assert "score 0.0125, score without literature 0.0; literature co-mention only." in lit
    assert mixed == ("Open Targets association between the targets of DRUGA+DRUGB and TERM_X (reaction x): score 0.5, "
                     f"score without literature 0.2. {TAIL}")


def test_memo_on_fixture_pairs():
    assert [i["id"] for i in omics.items_for_memo(omics.pair("NIRAPARIB", "thrombocytopenia"))] == [
        "omics:target:NIRAPARIB:PARP1@OT25.09", "omics:target:NIRAPARIB:PARP2@OT25.09",
        "omics:gtex:PARP1:Whole_Blood@gtex_v10", "omics:gtex:PARP2:Whole_Blood@gtex_v10",
        "omics:assoc:NIRAPARIB:HP_0001873@OT25.09"]
    assert [i["id"] for i in omics.items_for_memo(omics.pair("CLOZAPINE", "catalepsy"))] == [
        "omics:target:CLOZAPINE:DRD2@OT25.09", "omics:safety:DRD2:EFO_0009845@OT25.09",
        "omics:assoc:CLOZAPINE:EFO_0009845@OT25.09"]
    assert [i["id"] for i in omics.items_for_memo(omics.pair("CLOZAPINE", "some unmapped term"))] == [
        "omics:target:CLOZAPINE:DRD2@OT25.09"]

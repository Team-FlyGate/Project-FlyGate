"""오믹스 근거를 내는 API 세 경로, /api/grade 의 omics 묶음, flygate omics 명령을 픽스처 추출로 네트워크 없이 봅니다."""
import gzip
import importlib.util
import json
import pathlib
import shutil

import pytest
from fastapi.testclient import TestClient

import index
from _fv import omics

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "omics_fixture.json.gz"
NIRAPARIB_IDS = ["omics:target:NIRAPARIB:PARP1@OT25.09", "omics:target:NIRAPARIB:PARP2@OT25.09",
                 "omics:gtex:PARP1:Whole_Blood@gtex_v10", "omics:gtex:PARP2:Whole_Blood@gtex_v10",
                 "omics:assoc:NIRAPARIB:HP_0001873@OT25.09"]
CLOZAPINE_MEMO_IDS = ["omics:target:CLOZAPINE:DRD2@OT25.09", "omics:safety:DRD2:EFO_0009845@OT25.09",
                      "omics:assoc:CLOZAPINE:EFO_0009845@OT25.09"]


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    shutil.copy(FIXTURE, tmp_path / "omics.json.gz")
    monkeypatch.setattr(omics, "DATA", tmp_path)
    monkeypatch.setattr(index, "_hits", {})
    omics._omics.cache_clear()
    yield tmp_path
    omics._omics.cache_clear()


@pytest.fixture(scope="module")
def client():
    return TestClient(index.app)


def layers(items):
    return [i["layer"] for i in items]


# ---------------------------------------------------------------- API
def test_drugs_route_lists_extract_drugs(client):
    assert client.get("/api/omics/drugs").json() == {"asof": "2026-10-26", "drugs": ["CLOZAPINE", "NIRAPARIB"]}


def test_pair_route_returns_record_items_and_memo_items(client):
    r = client.get("/api/omics", params={"drug": "niraparib", "pt": "Thrombocytopenia"})
    assert r.status_code == 200
    body = r.json()
    assert (body["drug"], body["pt"], body["asof"]) == ("NIRAPARIB", "thrombocytopenia", "2026-10-26")
    assert body["pair"]["mapping"] == "label" and body["pair"]["safety_recorded"] is False
    assert [i["id"] for i in body["items"]] == NIRAPARIB_IDS
    assert layers(body["items"]) == ["L1", "L1", "L3", "L3", "L4"]
    assert [i["id"] for i in body["memo_items"]] == NIRAPARIB_IDS


def test_pair_route_matched_liability(client):
    body = client.get("/api/omics", params={"drug": "CLOZAPINE", "pt": "catalepsy"}).json()
    assert [(i["id"], i["match"]) for i in body["items"] if i["layer"] == "L2"] == [
        ("omics:safety:DRD2:EFO_0009845@OT25.09", "term"), ("omics:safety:DRD2:placeholder-liability@OT25.09", "none")]
    assert [i["id"] for i in body["memo_items"]] == CLOZAPINE_MEMO_IDS


def test_drug_route_lists_pairs(client):
    body = client.get("/api/omics", params={"drug": "clozapine"}).json()
    assert (body["drug"], body["asof"]) == ("CLOZAPINE", "2026-10-26") and "pt" not in body
    assert [(p["pt"], p["mapping"]) for p in body["pairs"]] == [("catalepsy", "label"), ("some unmapped term", "none")]


def test_unknown_drug_and_pair_are_404_with_detail(client):
    r = client.get("/api/omics", params={"drug": "OLAPARIB"})
    assert (r.status_code, r.json()["detail"]) == (404, "OLAPARIB is not in the omics extract")
    r = client.get("/api/omics", params={"drug": "OLAPARIB", "pt": "thrombocytopenia"})
    assert (r.status_code, r.json()["detail"]) == (404, "OLAPARIB is not in the omics extract")
    r = client.get("/api/omics", params={"drug": "NIRAPARIB", "pt": "anaemia"})
    assert (r.status_code, r.json()["detail"]) == (404, "NIRAPARIB|anaemia is not in the omics extract")


def test_missing_drug_is_422(client):
    assert client.get("/api/omics", params={"pt": "thrombocytopenia"}).status_code == 422


def test_pt_with_slash_is_a_query_value(client, data):
    with gzip.open(FIXTURE, "rt") as f:
        x = json.load(f)
    x["pairs"]["NIRAPARIB|fake/slash term"] = x["pairs"]["NIRAPARIB|thrombocytopenia"]
    with gzip.open(data / "omics.json.gz", "wt") as f:
        json.dump(x, f)
    omics._omics.cache_clear()
    body = client.get("/api/omics", params={"drug": "NIRAPARIB", "pt": "Fake/Slash Term"}).json()
    assert body["pt"] == "fake/slash term" and [i["id"] for i in body["items"]] == NIRAPARIB_IDS


def test_omics_routes_are_rate_limited(client, monkeypatch):
    monkeypatch.setitem(index.LIMIT, "omics", (1, 60))
    assert client.get("/api/omics/drugs").status_code == 200
    r = client.get("/api/omics", params={"drug": "NIRAPARIB"})
    assert (r.status_code, r.json()["detail"]) == (429, "rate limit: 1 omics calls per 60s")


# ---------------------------------------------------------------- /api/grade
@pytest.fixture
def offline_grade(monkeypatch):
    async def label(drug, pts, client, route=None):
        return {"found": False, "hits": [], "by_pt": {}}

    async def lit(drug, pt, client):
        return {"summary": {"read": 0}, "articles": [], "ids": []}

    async def know(drug, pt, client=None):
        return {"p": None}
    monkeypatch.setattr(index.evidence, "label_lookup", label)
    monkeypatch.setattr(index.evidence, "faers_2x2", lambda drug, pt: None)
    monkeypatch.setattr(index.literature, "read", lit)
    monkeypatch.setattr(index.knowledge, "recognize", know)


def test_grade_carries_omics_block(client, offline_grade):
    g = client.get("/api/grade", params={"drug": "NIRAPARIB", "pt": "thrombocytopenia"}).json()
    assert g["omics"] == {"count": 5, "memo_count": 5, "mapping": "label", "found": True}
    g = client.get("/api/grade", params={"drug": "CLOZAPINE", "pt": "catalepsy"}).json()
    assert g["omics"] == {"count": 7, "memo_count": 3, "mapping": "label", "found": True}


def test_grade_outside_extract_has_empty_omics_block_and_same_grade(client, offline_grade):
    inside = client.get("/api/grade", params={"drug": "NIRAPARIB", "pt": "thrombocytopenia"}).json()
    outside = client.get("/api/grade", params={"drug": "NIRAPARIB", "pt": "anaemia"}).json()
    assert outside["omics"] == {"count": 0, "memo_count": 0, "mapping": None, "found": False}
    assert (outside["grade"], outside["pv_class"]) == (inside["grade"], inside["pv_class"])


# ---------------------------------------------------------------- CLI
@pytest.fixture(scope="module")
def flygate():
    spec = importlib.util.spec_from_file_location("flygate", ROOT / "agent" / "flygate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_cli(flygate, capsys, *argv):
    code = flygate.main(["omics", *argv])
    return code, json.loads(capsys.readouterr().out)


def test_cli_found_prints_all_items_with_evidence_ids(flygate, capsys):
    code, out = run_cli(flygate, capsys, "niraparib", "Thrombocytopenia")
    assert code == 0
    assert {k: out[k] for k in ("cmd", "drug", "pt", "found", "asof", "mapping")} == {
        "cmd": "omics", "drug": "NIRAPARIB", "pt": "thrombocytopenia", "found": True, "asof": "2026-10-26",
        "mapping": "label"}
    assert "reason" not in out
    assert layers(out["items"]) == ["L1", "L1", "L3", "L3", "L4"]
    assert out["evidence_ids"] == NIRAPARIB_IDS


def test_cli_memo_flag_keeps_only_memo_items(flygate, capsys):
    _, out = run_cli(flygate, capsys, "CLOZAPINE", "catalepsy", "--memo")
    assert out["evidence_ids"] == CLOZAPINE_MEMO_IDS
    assert [i["match"] for i in out["items"] if i["layer"] == "L2"] == ["term"]


@pytest.mark.parametrize("drug,pt,reason", [
    ("OLAPARIB", "thrombocytopenia", "OLAPARIB is not in the omics extract"),
    ("NIRAPARIB", "anaemia", "NIRAPARIB|anaemia is not in the omics extract"),
])
def test_cli_not_found_exits_zero_with_reason(flygate, capsys, drug, pt, reason):
    code, out = run_cli(flygate, capsys, drug, pt)
    assert code == 0
    assert out == {"cmd": "omics", "drug": drug, "pt": pt, "found": False, "reason": reason, "asof": "2026-10-26",
                   "mapping": None, "items": [], "evidence_ids": []}


def test_pair_response_carries_term_record():
    c = TestClient(index.app)
    r = c.get("/api/omics", params={"drug": "NIRAPARIB", "pt": "thrombocytopenia"}).json()
    assert r["term"]["id"] == "HP_0001873"
    assert r["term"]["organs"]["sites"] == ["Blood"]
    r = c.get("/api/omics", params={"drug": "CLOZAPINE", "pt": "some unmapped term"}).json()
    assert r["term"] is None

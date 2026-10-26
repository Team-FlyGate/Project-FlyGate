"""근거 묶음에 들어가는 오믹스 항목, 크리틱 R14, 등급 공백 한 줄을 티켓 01 의 추출 파일로 네트워크 없이 검사합니다."""
import asyncio
import pathlib
import re
import shutil

import pytest

from _fv import assess, evidence, grade, literature, omics

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "omics_fixture.json.gz"
OMICS_GAP = "오믹스 근거는 등급에 반영하지 않음"


@pytest.fixture(autouse=True)
def offline(tmp_path, monkeypatch):
    shutil.copy(FIXTURE, tmp_path / "omics.json.gz")
    monkeypatch.setattr(omics, "DATA", tmp_path)
    omics._omics.cache_clear()

    async def fake_lookup(drug, pts, client, route=None):
        return {"found": False}

    async def fake_read(drug, pt, client, *a, **k):
        return {"query": "q", "count": 0, "pmids": [], "ids": [], "articles": [], "summary": {}}
    monkeypatch.setattr(evidence, "label_lookup", fake_lookup)
    monkeypatch.setattr(literature, "read", fake_read)
    monkeypatch.setattr(evidence, "faers_2x2", lambda drug, pt: None)
    yield
    omics._omics.cache_clear()


def bundle(drug, *reactions):
    case = {"primaryid": "1", "reactions": list(reactions), "drugs": [{"drug": drug, "role": "PS"}]}
    return asyncio.run(evidence.bundle(case, drug))


def omics_ids(b):
    return sorted(i for i in b["ids"] if i.startswith("omics:"))


def test_niraparib_bundle_carries_memo_items_without_safety():
    b = bundle("NIRAPARIB", "thrombocytopenia")
    assert omics_ids(b) == [
        "omics:assoc:NIRAPARIB:HP_0001873@OT25.09",
        "omics:gtex:PARP1:Whole_Blood@gtex_v10",
        "omics:gtex:PARP2:Whole_Blood@gtex_v10",
        "omics:target:NIRAPARIB:PARP1@OT25.09",
        "omics:target:NIRAPARIB:PARP2@OT25.09",
    ]
    assert b["omics"] == {"thrombocytopenia": {"found": True, "mapping": "label", "n_memo": 5}}
    what = {c["id"]: c["what"] for c in b["catalog"]}
    assert what["omics:assoc:NIRAPARIB:HP_0001873@OT25.09"].startswith("Open Targets association between")
    assert "literature co-mention only" in what["omics:assoc:NIRAPARIB:HP_0001873@OT25.09"]


def test_clozapine_bundle_keeps_matched_liability_only():
    b = bundle("CLOZAPINE", "catalepsy")
    assert omics_ids(b) == [
        "omics:assoc:CLOZAPINE:EFO_0009845@OT25.09",
        "omics:safety:DRD2:EFO_0009845@OT25.09",
        "omics:target:CLOZAPINE:DRD2@OT25.09",
    ]
    assert "omics:safety:DRD2:placeholder-liability@OT25.09" not in b["ids"]


def test_shared_target_items_appear_once_across_reactions():
    b = bundle("CLOZAPINE", "catalepsy", "some unmapped term")
    assert [c["id"] for c in b["catalog"]].count("omics:target:CLOZAPINE:DRD2@OT25.09") == 1
    assert b["omics"]["some unmapped term"] == {"found": True, "mapping": "none", "n_memo": 1}


def test_reaction_outside_extract_adds_nothing():
    b = bundle("NIRAPARIB", "nausea")
    assert omics_ids(b) == []
    assert b["omics"] == {"nausea": {"found": False, "mapping": None, "n_memo": 0}}


def test_missing_extract_adds_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(omics, "DATA", tmp_path / "absent")
    omics._omics.cache_clear()
    b = bundle("NIRAPARIB", "thrombocytopenia")
    assert omics_ids(b) == []
    assert b["omics"] == {"thrombocytopenia": {"found": False, "mapping": None, "n_memo": 0}}


R14 = ("Mechanistic evidence (target safety liabilities, tissue expression, target-disease association) shows biological "
       "plausibility at the population level. It never establishes that the drug caused the reaction in this case, and "
       "absence of mechanistic evidence is not evidence against the association.")


def test_r14_in_rules_and_system_prompt():
    assert dict(assess.OVERCLAIM_RULES)["R14"] == R14
    assert f"R14: {R14}" in assess.SYSTEM


def test_tier1_accepts_bundle_omics_id_and_rejects_unknown_one():
    ids = set(bundle("NIRAPARIB", "thrombocytopenia")["ids"])
    ok = [{"id": "c1", "text": "PARP1 is a target.", "evidence": ["omics:target:NIRAPARIB:PARP1@OT25.09"]}]
    bad = [{"id": "c1", "text": "PARP3 is a target.", "evidence": ["omics:target:NIRAPARIB:PARP3@OT25.09"]}]
    assert assess.tier1_rules(ok, ids) == []
    assert [i["rule"] for i in assess.tier1_rules(bad, ids)] == ["unknown_evidence"]


def test_grade_gaps_state_omics_not_graded():
    f = {"id": "faers:2x2:X:rash@2026Q2", "a": 50, "evans": True, "ror_sig": True, "ic_sig": True,
         "prr": 3.0, "prr_lo": 2.0, "prr_hi": 4.0, "ror_lo": 2.1, "ic025": 1.2, "chi2": 40}
    label = {"found": True, "hits": [{"id": "label:S#warnings_and_cautions", "pt": "rash"}],
             "by_pt": {"rash": {"sections": ["warnings_and_cautions"], "rank": 2, "disclaimer": None}}}
    g = grade.grade_pair("X", "rash", f, label, {"summary": {"read": 0}})
    assert g["gaps"][-1] == OMICS_GAP and g["gaps"].count(OMICS_GAP) == 1
    gc = (ROOT / "web/src/components/GradeCard.tsx").read_text()
    assert f"'{OMICS_GAP}': 'Omics evidence is not reflected in the grade'" in gc


def test_rule_count_matches_every_place_that_lists_rules():
    keys = [k for k, _ in assess.OVERCLAIM_RULES]
    n = len(keys)
    assert keys == [f"R{i}" for i in range(1, n + 1)]
    skills = (ROOT / "web/src/pages/Skills.tsx").read_text()
    assert re.findall(r"\['(R\d+)', t\(", skills) == keys
    glossary = (ROOT / "web/src/lib/glossary.ts").read_text()
    assert f"{n}가지 규칙(R1–R{n})" in glossary and f"{n} rules (R1–R{n})" in glossary
    critic = (ROOT / "skills/pv-critic/SKILL.md").read_text()
    rules_line = next(line for line in critic.splitlines() if line.startswith("Rules R1–"))
    assert critic.count(f"R1–R{n}") == 2 and f"R1–R{n}" in rules_line and "mechanistic plausibility" in rules_line

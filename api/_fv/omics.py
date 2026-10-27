"""오믹스 근거 층입니다. 빌드 시점에 공개 DB 에서 뽑은 추출 파일 omics.json.gz 만 읽고, 근거 항목은 요청 시점에 표에서 짭니다.

omics:target:<DRUG>:<SYMBOL>@OT<ver>                L1 약물의 작용 기전 표적 (Open Targets)
omics:safety:<SYMBOL>:<eventId or slug>@OT<ver>     L2 표적의 안전성 책임 (Open Targets safetyLiabilities). eventId 가 없으면 사건명 slug
omics:gtex:<SYMBOL>:<tissueSiteDetailId>@gtex_v10   L3 표적의 조직별 발현 중앙값 TPM (GTEx v10)
omics:assoc:<DRUG>:<termId>@OT<ver>                 L4 표적-질환 연관 점수와 문헌 동시 언급만 근거인지 여부 (Open Targets)

DRUG 는 evidence.id_drug 형태(역슬래시를 + 로)이고, 쌍 키는 signals.json.gz 형태 그대로 <DRUG>|<pt 소문자> 입니다.
terms[].organs.sites 는 GTEx 조직 묶음(tissueSite) 이름이라, gtex_tissues 표(tissueSiteDetailId -> tissueSite)로
세부 조직을 풉니다. 빠진 값은 null 이며 0 으로 채우지 않습니다. what 문장은 쌍과 무관한 사실만 적어 같은 ID 는
어느 묶음에서나 같은 문장이고, 모두 개별 사례의 인과가 아니라는 문장으로 끝납니다.
"""
import functools
import gzip
import json
import re

from .config import DATA
from .evidence import id_drug

TAIL = "Population-level mechanistic context; not evidence that the drug caused this reaction in this case."


@functools.lru_cache(maxsize=1)
def _omics():
    p = DATA / "omics.json.gz"
    if not p.exists():
        return {"asof": None, "versions": {}, "gtex_tissues": {}, "drugs": {}, "targets": {}, "terms": {},
                "pairs": {}, "errors": []}
    with gzip.open(p, "rt") as f:
        return json.load(f)


def drugs() -> list[str]:
    return sorted(_omics()["drugs"])


def _record(drug: str, pt: str) -> dict | None:
    o = _omics()
    p = o["pairs"].get(f"{drug}|{pt}")
    if p is None:
        return None
    term = o["terms"].get(p.get("term")) or {}
    targets = [o["targets"][t] for t in o["drugs"][drug]["targets"]]
    return {"drug": drug, "pt": pt, "term": p.get("term"), "mapping": term.get("match", "none"),
            "safety_match": p.get("safety_match"), "assoc": p.get("assoc"),
            "safety_recorded": any(t.get("safety") is not None for t in targets)}


def pair(drug: str, pt: str) -> dict | None:
    return _record(drug.upper(), pt.lower())


def drug_pairs(drug: str) -> list[dict] | None:
    d = drug.upper()
    if d not in _omics()["drugs"]:
        return None
    return [_record(d, k.split("|", 1)[1]) for k in sorted(_omics()["pairs"]) if k.split("|", 1)[0] == d]


def _shown(x) -> str:
    if x is None:
        return "not recorded"
    return str(round(x, 4)) if isinstance(x, float) else str(x)


def _target_item(drug: str, ensg: str, t: dict, ot: str) -> dict:
    sym, safety = t["symbol"], t.get("safety")
    moa = "; ".join(f"{m['action']}, {m['mechanism']}" for m in t["moa"] if m["drug"] == drug)
    if safety is None:
        lia = f"Open Targets records no safety liability field for {sym} (nothing recorded, not zero)."
    else:
        lia = f"Open Targets lists {len(safety)} safety liabilities for {sym}."
    return {"id": f"omics:target:{id_drug(drug)}:{sym}@{ot}", "layer": "L1",
            "what": f"{sym} ({ensg}) is a mechanism-of-action target of {id_drug(drug)} in Open Targets: {moa}. "
                    f"{lia} {TAIL}",
            "n": {"liabilities": None if safety is None else len(safety)}}


def _safety_item(sym: str, s: dict, ot: str, match: str) -> dict:
    key = s["event_id"] or re.sub(r"[^a-z0-9]+", "-", s["event"].lower()).strip("-")
    tissues = ", ".join(s["tissue_ids"]) if s["tissue_ids"] else "not recorded"
    return {"id": f"omics:safety:{sym}:{key}@{ot}", "layer": "L2",
            "what": f"Open Targets safety liability of {sym}: {s['event']} ({s['event_id'] or 'no event ID'}); "
                    f"tissues {tissues}; source {_shown(s['datasource'])}, PMID {_shown(s['pmid'])}. {TAIL}",
            "n": None, "match": match}


def _gtex_items(sym: str, gtex: dict | None, groups: list | None, sites: dict, ver: str) -> list[dict]:
    tpm = {k: v for k, v in (gtex or {}).items() if v is not None}
    ranked = sorted(tpm, key=lambda k: -tpm[k])
    picked = ranked[:5] if groups is None else [k for k in ranked if sites.get(k) in groups]
    out = []
    for k in picked:
        rank = 1 + sum(v > tpm[k] for v in tpm.values())
        out.append({"id": f"omics:gtex:{sym}:{k}@{ver}", "layer": "L3",
                    "what": f"GTEx ({ver}) median expression of {sym} in {k} (tissue group {sites.get(k)}): "
                            f"{tpm[k]} TPM, rank {rank} of {len(tpm)} tissues. {TAIL}",
                    "n": {"median_tpm": tpm[k], "rank_of_54": rank}})
    return out


def _assoc_item(drug: str, term: dict, a: dict, ot: str) -> dict:
    what = f"the targets of {id_drug(drug)} and {term['id']} ({term['label']})"
    if not a["row_found"]:
        what = f"Open Targets has no association row between {what}; nothing recorded, not a zero score."
    else:
        what = (f"Open Targets association between {what}: score {_shown(a['score'])}, "
                f"score without literature {_shown(a['score_no_literature'])}")
        what += "; literature co-mention only." if (a["score"] or 0) > 0 and a["score_no_literature"] == 0 else "."
    return {"id": f"omics:assoc:{id_drug(drug)}:{term['id']}@{ot}", "layer": "L4", "what": f"{what} {TAIL}",
            "n": {"score": a["score"], "score_no_literature": a["score_no_literature"]}}


def _term(rec: dict) -> dict | None:
    return _omics()["terms"][rec["term"]] if rec["mapping"] != "none" else None


def _groups(rec: dict) -> list | None:
    return ((_term(rec) or {}).get("organs") or {}).get("sites")


def items(rec: dict) -> list[dict]:
    """쌍의 L1-L4 근거 항목 전부입니다(대시보드·CLI). 층 순서로 내고, 층 안에서는 약물의 표적 순서를 따릅니다."""
    o = _omics()
    ot, ver = f"OT{o['versions'].get('opentargets')}", o["versions"].get("gtex")
    targets = [(e, o["targets"][e]) for e in o["drugs"][rec["drug"]]["targets"]]
    matched = {(m["target"], m["index"]): m["relation"] for m in rec["safety_match"] or []}
    term, groups = _term(rec), _groups(rec)
    l1 = [_target_item(rec["drug"], e, t, ot) for e, t in targets]
    l2 = [_safety_item(t["symbol"], s, ot, matched.get((e, i), "none"))
          for e, t in targets for i, s in enumerate(t.get("safety") or [])]
    l3 = [x for _, t in targets for x in _gtex_items(t["symbol"], t.get("gtex"), groups, o["gtex_tissues"], ver)]
    l4 = [_assoc_item(rec["drug"], term, rec["assoc"], ot)] if term and rec["assoc"] is not None else []
    return l1 + l2 + l3 + l4


def items_for_memo(rec: dict) -> list[dict]:
    """System-2 메모에 넣는 몫입니다. L1 5개, term·ancestor 로 맞은 L2, 후보 조직 안 L3 중 TPM 상위 5개, L4 1개."""
    its = items(rec)
    by = {layer: [i for i in its if i["layer"] == layer] for layer in ("L1", "L2", "L3", "L4")}
    l3 = sorted(by["L3"], key=lambda i: -i["n"]["median_tpm"])[:5] if _groups(rec) is not None else []
    return by["L1"][:5] + [i for i in by["L2"] if i["match"] != "none"] + l3 + by["L4"]

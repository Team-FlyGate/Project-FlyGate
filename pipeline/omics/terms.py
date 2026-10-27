"""PT to ontology term mapping and organ candidates (design section 3).

A PT maps only on an exact label or synonym match against its labeltext variants, searched in OLS (EFO), HPO,
then Mondo. There is no parent roll-up. Organ candidates are the GTEx tissue groups that share a word with the
label or synonyms of one of the term's HP ancestors.
"""
import pathlib
import re
import sys

API = pathlib.Path(__file__).resolve().parents[2] / "api"
if str(API) not in sys.path:
    sys.path.insert(0, str(API))
from _fv import labeltext  # noqa: E402

SEARCHES = (
    ("ols_efo", "ols_search_efo_terms", lambda q: {"query": q, "rows": 5},
     lambda d: [(t.get("short_form") or t.get("obo_id"), t.get("label"), []) for t in d.get("terms") or []]),
    ("hpo", "HPO_search_terms", lambda q: {"query": q, "max_results": 5},
     lambda d: [(t.get("id"), t.get("name"), t.get("synonyms") or []) for t in d or []]),
    ("mondo", "Mondo_search_disease", lambda q: {"query": q, "limit": 5},
     lambda d: [(t.get("id"), t.get("name"), t.get("synonyms") or []) for t in d or []]),
)
OT_NO_DISEASE = "OpenTargets returned no disease for ID"
UNMAPPED = {"id": None, "label": None, "match": "none", "source": None, "ancestors": None, "organs": None}


def norm_id(x: str) -> str:
    return x.replace(":", "_")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().replace("-", " ")).strip()


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def variants(pt: str) -> set[str]:
    return {_norm(v) for v in labeltext.us_variants(pt) + labeltext.equivalents(pt)}


def search_text(pt: str) -> str:
    """The US spelling when it differs, because OLS does not find 'anaemia' terms by the UK form."""
    return next((v for v, via in labeltext.variants(pt) if via == "spelling"), _norm(pt))


def _match(hit: tuple, want: set[str]) -> str | None:
    _, label, synonyms = hit
    if label and _norm(label) in want:
        return "label"
    return "synonym" if any(_norm(s) in want for s in synonyms) else None


def map_term(f, pt: str, groups: list[str]) -> dict:
    want, q, first = variants(pt), search_text(pt), None
    for source, tool, args, parse in SEARCHES:
        data = f.tool(tool, args(q))
        hits = [h for h in (parse(data) if data is not None else []) if h[0]]
        for hit in hits:
            kind = _match(hit, want)
            if kind:
                tid = norm_id(hit[0])
                anc = ancestors(f, tid)
                return {"id": tid, "label": hit[1], "match": kind, "source": source, "ancestors": anc,
                        "organs": organs(f, anc, groups)}
        if hits and first is None:
            first = {"id": norm_id(hits[0][0]), "label": hits[0][1], "source": source}
    return {**UNMAPPED, "first_hit": first} if first else dict(UNMAPPED)


def ancestors(f, tid: str) -> list[str] | None:
    """Open Targets ancestors, else the HPO parents walk for HP terms, else None with an error entry."""
    d = f.tool("OpenTargets_get_disease_ancestors_parents_by_efoId", {"efoId": tid}, absent=OT_NO_DISEASE)
    disease = (d or {}).get("disease")
    if disease is not None and disease.get("ancestors") is not None:
        return [norm_id(a) for a in disease["ancestors"]]
    walked = _hpo_walk(f, tid) if tid.startswith("HP_") else None
    if walked is None:
        f.note("build", {"ancestors": tid}, "no_ancestors")
    return walked


def _hpo_walk(f, tid: str) -> list[str] | None:
    seen, queue = [], [tid]
    while queue:
        d = f.tool("HPO_get_term_hierarchy", {"term_id": queue.pop(0).replace("_", ":"), "direction": "parents"})
        if d is None:
            return None
        for p in d:
            pid = norm_id(p["id"])
            if pid not in seen:
                seen.append(pid)
                queue.append(pid)
    return seen


def organs(f, ancestor_ids: list[str] | None, groups: list[str]) -> dict | None:
    """조직 그룹 이름의 단어가 모두 HP 상위 용어의 라벨·동의어에 들어 있을 때만 후보로 둡니다. 'blood' 하나로 Blood Vessel 까지 잡지 않기 위해서입니다."""
    if not ancestor_ids:
        return None
    evidence, sites = [], set()
    for a in ancestor_ids:
        if not a.startswith("HP_"):
            continue
        d = f.tool("HPO_get_term", {"term_id": a.replace("_", ":")})
        if d is None:
            continue
        have = _words(" ".join([d.get("name") or "", *(d.get("synonyms") or [])]))
        for g in groups:
            need = _words(g)
            if need and need <= have:
                evidence.append({"ancestor": a, "word": " ".join(sorted(need))})
                sites.add(g)
    if not evidence:
        return None
    return {"sites": sorted(sites), "method": "hpo_ancestor_label", "evidence": evidence}

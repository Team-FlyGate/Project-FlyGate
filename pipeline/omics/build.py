"""Builds api/_data/omics.json.gz from public databases. See pipeline/omics/README.md.

python -m pipeline.omics.build --drugs pipeline/omics/drugs_v1.txt --pairs pipeline/omics/pairs_v1.txt --cases \
    --out api/_data/omics.json.gz [--dry-run] [--limit N]
"""
import argparse
import gzip
import json
import pathlib

from . import layers, terms
from .fetch import HOSTS, TOOLUNIVERSE, Fetcher
from .terms import labeltext

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "api" / "_data"


def read_lines(path: pathlib.Path) -> list[str]:
    return [s for s in (x.strip() for x in path.read_text(encoding="utf-8").splitlines()) if s and not s.startswith("#")]


def read_pairs(path: pathlib.Path) -> list[tuple[str, str]]:
    return [(d.strip().upper(), p.strip().lower()) for d, p in (x.split("\t", 1) for x in read_lines(path))]


def _gz(path: pathlib.Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def signal_pts(n: int) -> dict[str, list[str]]:
    """Top-n PTs per drug in signals.json.gz order, as evidence.drug_profile returns them."""
    if n <= 0:
        return {}
    s = _gz(DATA / "signals.json.gz")
    col = s["columns"].index("pt")
    return {d: [r[col] for r in rows[:n]] for d, rows in s["drugs"].items()}


def case_pairs() -> list[tuple[str, str]]:
    """Each demo case's primary-suspect drug with its top 3 reactions, chosen as evidence.bundle chooses them."""
    out = []
    for c in _gz(DATA / "cases.json.gz"):
        rx = c.get("reactions", [])
        pts = [p for p in rx if not labeltext.is_nonclinical(p)][:3] or rx[:3]
        out += [(d["drug"].upper(), p.lower()) for d in c.get("drugs", []) if d.get("role") == "PS" for p in pts]
    return out


def plan(drugs: list[str], explicit: list[tuple[str, str]], top: dict[str, list[str]],
         cases: list[tuple[str, str]], limit: int | None) -> tuple[dict[str, list[str]], set[str]]:
    """Ordered `{drug: [pt, ...]}` and the distinct nonclinical PTs dropped."""
    order = list(dict.fromkeys([d.upper() for d in drugs] + [d for d, _ in cases] + [d for d, _ in explicit]))
    order = order[:limit] if limit else order
    want: dict[str, list[str]] = {d: [p.lower() for p in top.get(d, [])] for d in order}
    for d, p in cases + explicit:
        if d in want:
            want[d].append(p)
    dropped = set()
    for d, pts in want.items():
        want[d] = [p for p in dict.fromkeys(pts) if not labeltext.is_nonclinical(p)]
        dropped |= set(pts) - set(want[d])
    return want, dropped


def build(f: Fetcher, want: dict[str, list[str]]) -> tuple[dict, dict]:
    """The extract, and the term table of every planned PT (the extract keeps only terms its pairs use)."""
    ot = layers.opentargets_version(f)
    ontologies = layers.ontology_versions(f)
    tissues = layers.gtex_tissues(f)
    if tissues is None and not f.dry_run:
        raise SystemExit("GTEx tissue list unavailable; every L3 record and organ candidate depends on it")
    tissues = tissues or {}
    groups = list(dict.fromkeys(tissues.values()))

    drugs, targets = {}, {}
    for name in want:
        r = layers.drug(f, name)
        if r is None:
            f.note("build", {"drug": name}, "drug_unresolved")
            continue
        flags = layers.dgidb(f, name, [r["moa"][e]["symbol"] for e in r["targets"]]) if r["targets"] else {}
        drugs[name] = {"chembl_id": r["chembl_id"], "match": r["match"], "targets": r["targets"]}
        for e in r["targets"]:
            sym = r["moa"][e]["symbol"]
            t = targets.setdefault(e, {"symbol": sym, "moa": [], "safety": None, "gtex": None})
            t["moa"] += [{"drug": name, "action": a, "mechanism": m, "dgidb": flags.get(sym)} for a, m in r["moa"][e]["rows"]]
    dumps = {}
    for e, t in targets.items():
        t["safety"] = layers.safety(f, e)
        t["gtex"] = layers.gtex(f, e, list(tissues))
        dumps[e] = layers.association_dump(f, e)

    term_table = {}
    for pts in want.values():
        for p in pts:
            if p not in term_table:
                term_table[p] = terms.map_term(f, p, groups)
    pairs = {}
    for name, d in drugs.items():
        for p in want[name]:
            term = term_table[p]
            pairs[f"{name}|{p}"] = {"term": p, "safety_match": layers.safety_match(term, d["targets"], targets),
                                    "assoc": layers.pair_assoc(term, d["targets"], dumps)}
    used = dict.fromkeys(v["term"] for v in pairs.values())
    return ({"asof": max(f.dates) if f.dates else None,
            "versions": {"tooluniverse": TOOLUNIVERSE, "opentargets": ot, "gtex": layers.GTEX, **ontologies},
            "gtex_tissues": tissues, "drugs": drugs, "targets": targets,
            "terms": {p: term_table[p] for p in used}, "pairs": pairs, "errors": f.errors}, term_table)


def write(extract: dict, out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(extract, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with open(out, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as gz:
        gz.write(body)


def _pct(k: int, n: int) -> str:
    return f"{k}/{n} ({100 * k / n:.1f}%)" if n else f"{k}/0"


def coverage(f: Fetcher, want: dict, dropped: set[str], x: dict, tt: dict) -> str:
    planned = {p for pts in want.values() for p in pts}
    kinds = {k: sum(1 for t in tt.values() if t["match"] == k) for k in ("label", "synonym", "none")}
    mapped = kinds["label"] + kinds["synonym"]
    tg = x["targets"].values()
    lines = [
        f"drugs      planned {len(want)}, in extract {len(x['drugs'])}, "
        f"with targets {sum(1 for d in x['drugs'].values() if d['targets'])}, "
        f"no exact Open Targets name {sum(1 for d in x['drugs'].values() if d['match'] == 'none')}",
        f"targets    {len(x['targets'])}, safety field present {sum(1 for t in tg if t['safety'] is not None)}, "
        f"gtex recorded {sum(1 for t in tg if t['gtex'] is not None)}",
        f"PTs        planned {len(planned)} (nonclinical dropped {len(dropped)}), label {kinds['label']}, "
        f"synonym {kinds['synonym']}, none {kinds['none']}",
        f"mapping    {_pct(mapped, len(tt))}",
        f"organs     {_pct(sum(1 for t in tt.values() if t['organs']), mapped)} of mapped terms",
        f"pairs      planned {sum(map(len, want.values()))}, in extract {len(x['pairs'])}, with assoc {sum(1 for v in x['pairs'].values() if v['assoc'])}",
        f"{'source':12} {'host':28} {'cached':>8} {'sent':>8} {'not_cached':>11} {'failed':>7}",
    ]
    tot = {"cached": 0, "sent": 0, "not_cached": 0, "failed": 0}
    for src in sorted(f.stats):
        s = f.stats[src]
        tot = {k: tot[k] + s[k] for k in tot}
        lines.append(f"{src:12} {HOSTS.get(src, '-'):28} {s['cached']:>8} {s['sent']:>8} {s['not_cached']:>11} "
                     f"{s['failed']:>7}")
    lines.append(f"{'total':12} {'':28} {tot['cached']:>8} {tot['sent']:>8} {tot['not_cached']:>11} {tot['failed']:>7}")
    lines.append(f"errors     {len(x['errors'])}")
    lines.append(f"versions   {json.dumps(x['versions'])}  asof {x['asof']}")
    return "\n".join(lines)


def dry_run_note(unresolved: int) -> str:
    """The calls a dry run cannot count, because their inputs come from responses that are not cached yet."""
    return (f"dry run    nothing written. not_cached is exact only for calls whose inputs are known. Still uncounted: "
            f"{unresolved} drugs not resolved from cache, each adding opentargets 1 (mechanisms) and dgidb 1, and per "
            f"target opentargets 2 (safety, associations) and gtex 1. PT searches are counted at their upper bound of "
            f"3 (ols, hpo, mondo); each PT that maps adds opentargets 1 (ancestors), and hpo 1 per new HP ancestor "
            f"(labels, or the parents walk when Open Targets lacks the term).")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the omics evidence extract")
    ap.add_argument("--drugs", type=pathlib.Path, required=True, help="one drug per line, signals.json.gz form")
    ap.add_argument("--pairs", type=pathlib.Path, help="DRUG<TAB>pt per line, added to the top-N PTs")
    ap.add_argument("--pts-per-drug", type=int, default=80, help="top PTs per drug from signals.json.gz")
    ap.add_argument("--cases", action="store_true", help="add each demo case's PS drug with its top 3 reactions")
    ap.add_argument("--out", type=pathlib.Path, default=DATA / "omics.json.gz")
    ap.add_argument("--dry-run", action="store_true", help="read the cache only and count the calls it would send")
    ap.add_argument("--limit", type=int, help="keep only the first N drugs")
    a = ap.parse_args(argv)

    want, dropped = plan(read_lines(a.drugs), read_pairs(a.pairs) if a.pairs else [], signal_pts(a.pts_per_drug),
                         case_pairs() if a.cases else [], a.limit)
    f = Fetcher(dry_run=a.dry_run)
    extract, term_table = build(f, want)
    print(coverage(f, want, dropped, extract, term_table))
    if a.dry_run:
        print(dry_run_note(len(want) - len(extract["drugs"])))
        return 0
    write(extract, a.out)
    print(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

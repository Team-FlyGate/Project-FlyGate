"""L1 to L4 queries and the pure reshaping of their responses into extract records.

L1 mechanism-of-action targets (Open Targets, cross-checked in DGIdb), L2 target safety liabilities (Open Targets),
L3 GTEx v10 median TPM per tissue, L4 target-disease association scores from the pilot's GraphQL with the
no-literature alias. A failed query is None; the Fetcher holds its error record.
"""
from .terms import norm_id

GTEX = "gtex_v10"
PAGE = 3000
NO_LITERATURE = [{"id": "europepmc", "weight": 0.0, "propagate": True}]
Q_META = "query Meta { meta { apiVersion { x y z } dataVersion { year month iteration } } }"
Q_ASSOC_DUMP = ("query TargetAssociationDump($id: String!, $page: Pagination!, $noLit: [DatasourceSettingsInput!]) "
                "{ target(ensemblId: $id) { id approvedSymbol all: associatedDiseases(page: $page) { count rows "
                "{ disease { id } score } } noLiterature: associatedDiseases(page: $page, datasources: $noLit) "
                "{ count rows { disease { id } score } } } }")
OLS_ONTOLOGY = "https://www.ebi.ac.uk/ols4/api/ontologies/{}"
ONTOLOGIES = (("ols_efo", "efo"), ("hpo", "hp"), ("mondo", "mondo"))


def opentargets_version(f) -> str | None:
    dv = (((f.graphql("Meta", Q_META, None) or {}).get("meta")) or {}).get("dataVersion") or {}
    if not dv.get("year") or not dv.get("month"):
        return None
    return ".".join([dv["year"], dv["month"]] + ([str(dv["iteration"])] if dv.get("iteration") else []))


def ontology_versions(f) -> dict:
    """Releases as loaded in OLS. The HPO and Mondo searches go to JAX and Monarch, which may serve another release."""
    return {k: ((f.get("ols", OLS_ONTOLOGY.format(o)) or {}).get("config") or {}).get("version") for k, o in ONTOLOGIES}


def gtex_tissues(f) -> dict | None:
    d = f.tool("GTEx_get_tissue_sites", {"dataset_id": GTEX})
    return None if d is None else {r["tissueSiteDetailId"]: r["tissueSite"] for r in d}


def drug(f, name: str) -> dict | None:
    """`{chembl_id, match, targets, moa: {ENSG: {symbol, rows: [(action, mechanism)]}}}`, or None if a call failed."""
    d = f.tool("OpenTargets_get_drug_chembId_by_generic_name", {"drugName": name})
    if d is None:
        return None
    hits = (d.get("search") or {}).get("hits") or []
    hit = next((h for h in hits if (h.get("name") or "").casefold() == name.casefold()), None)
    if hit is None:
        return {"chembl_id": None, "match": "none", "targets": [], "moa": {}}
    m = f.tool("OpenTargets_get_drug_mechanisms_of_action_by_chemblId", {"chemblId": hit["id"]})
    if m is None:
        return None
    moa: dict[str, dict] = {}
    for row in ((m.get("drug") or {}).get("mechanismsOfAction") or {}).get("rows") or []:
        for t in row.get("targets") or []:
            entry = moa.setdefault(t["id"], {"symbol": t.get("approvedSymbol"), "rows": []})
            am = (row.get("actionType"), row.get("mechanismOfAction"))
            if am not in entry["rows"]:
                entry["rows"].append(am)
    return {"chembl_id": hit["id"], "match": "name_exact", "targets": list(moa), "moa": moa}


def dgidb(f, name: str, symbols: list[str]) -> dict:
    """Per symbol: True if DGIdb lists this drug for the gene, False if the gene lacks it, None if DGIdb has no gene."""
    d = f.tool("DGIdb_get_drug_gene_interactions", {"genes": symbols})
    nodes = {n.get("name"): n for n in ((d or {}).get("genes") or {}).get("nodes") or []}
    return {s: (any(((i.get("drug") or {}).get("name") or "").casefold() == name.casefold()
                    for i in nodes[s].get("interactions") or []) if s in nodes else None) for s in symbols}


def _join(*parts: str | None) -> str | None:
    out = list(dict.fromkeys(x for p in parts if p for x in p.split(";")))
    return ";".join(out) or None


def _pmids(literature) -> str | None:
    if isinstance(literature, list):
        return _join(*(str(x) for x in literature))
    return None if literature is None else str(literature)


def merge_liabilities(raw: list[dict]) -> list[dict]:
    """Open Targets can list one eventId once per datasource. Those merge into one liability so IDs stay unique."""
    out, by_id = [], {}
    for s in raw:
        lia = {"event": s.get("event"), "event_id": norm_id(s["eventId"]) if s.get("eventId") else None,
               "tissue_ids": list(dict.fromkeys(norm_id(b["tissueId"]) for b in s.get("biosamples") or []
                                                if b.get("tissueId"))),
               "datasource": s.get("datasource"), "pmid": _pmids(s.get("literature"))}
        prev = by_id.get(lia["event_id"]) if lia["event_id"] else None
        if prev is None:
            out.append(lia)
            if lia["event_id"]:
                by_id[lia["event_id"]] = lia
            continue
        prev["tissue_ids"] += [t for t in lia["tissue_ids"] if t not in prev["tissue_ids"]]
        prev["datasource"] = _join(prev["datasource"], lia["datasource"])
        prev["pmid"] = _join(prev["pmid"], lia["pmid"])
    return out


def safety(f, ensg: str) -> list[dict] | None:
    """None when the call failed or when Open Targets has no `safetyLiabilities` field; [] when the field is empty."""
    d = f.tool("OpenTargets_get_target_safety_profile_by_ensemblID", {"ensemblId": ensg})
    raw = ((d or {}).get("target") or {}).get("safetyLiabilities")
    return None if raw is None else merge_liabilities(raw)


def gtex(f, ensg: str, tissues: list[str]) -> dict | None:
    d = f.tool("GTEx_get_median_gene_expression", {"gencode_id": ensg, "dataset_id": GTEX})
    if not d:
        return None
    median = {r["tissueSiteDetailId"]: r.get("median") for r in d}
    return {t: median.get(t) for t in tissues}


def association_dump(f, ensg: str) -> dict | None:
    """Every association row of the target, `{disease_id: (score, score_no_literature)}`, paged as in the pilot."""
    rows, nolit, index = {}, {}, 0
    while True:
        variables = {"id": ensg, "page": {"index": index, "size": PAGE}, "noLit": NO_LITERATURE}
        d = f.graphql("TargetAssociationDump", Q_ASSOC_DUMP, variables)
        node = (d or {}).get("target")
        if node is None:
            if d is not None:
                f.note("opentargets", {"target": ensg}, "target_not_in_opentargets")
            return None
        for r in node["all"]["rows"]:
            rows[r["disease"]["id"]] = float(r["score"])
        for r in node["noLiterature"]["rows"]:
            nolit[r["disease"]["id"]] = float(r["score"])
        index += 1
        if index * PAGE >= max(node["all"]["count"], node["noLiterature"]["count"]):
            return {k: (v, nolit.get(k, 0.0)) for k, v in rows.items()}


def pair_assoc(term: dict, targets: list[str], dumps: dict) -> dict | None:
    """Max over the drug's targets. A row absent from the no-literature alias scores 0.0, as in the pilot."""
    if term["id"] is None or term["ancestors"] is None or not targets:
        return None
    if any(dumps.get(e) is None for e in targets):
        return None
    found = [dumps[e][term["id"]] for e in targets if term["id"] in dumps[e]]
    if not found:
        return {"score": None, "score_no_literature": None, "row_found": False}
    return {"score": max(s for s, _ in found), "score_no_literature": max(n for _, n in found), "row_found": True}


def safety_match(term: dict, targets: list[str], target_records: dict) -> list[dict] | None:
    if term["id"] is None:
        return None
    anc = set(term["ancestors"] or [])
    out = []
    for e in targets:
        for i, s in enumerate(target_records[e]["safety"] or []):
            rel = "term" if s["event_id"] == term["id"] else "ancestor" if s["event_id"] in anc else None
            if rel:
                out.append({"target": e, "index": i, "relation": rel})
    return out

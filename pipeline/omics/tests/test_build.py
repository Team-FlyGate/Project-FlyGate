"""Build tests, offline. Responses go into a temporary cache through the real cache rule, and every test runs with
the network calls replaced by a test failure, so a request missing from the cache cannot reach the network.

Values copied from responses queried on 2026-10-26 are the HPO thrombocytopenia and anemia hits, the HP ancestor
labels, and the two DRD2 "confusion" liabilities. Everything else is shaped test data, not a biological claim.
"""
import pathlib

import pytest

from pipeline.omics import build, fetch, layers, terms
from pipeline.omics.fetch import Fetcher, cache_path, source_of, write_entry

HERE = pathlib.Path(__file__).resolve().parent
FIXTURE = HERE.parents[2] / "tests" / "fixtures" / "omics_fixture.json.gz"


def tool(name, arguments, response):
    return source_of(name), {"tool": name, "arguments": arguments}, response


def cached(root: pathlib.Path, *entries) -> Fetcher:
    for source, key, response in entries:
        write_entry(cache_path(root, source, key), key, "2026-10-26", response)
    return Fetcher(root=root, gap=0)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*_a, **_k):
        pytest.fail("network used")
    monkeypatch.setattr(fetch, "_send", refuse)
    monkeypatch.setattr(fetch, "_toolu", refuse)


def test_cache_replay_reproduces_fixture_bytes(tmp_path, monkeypatch):
    monkeypatch.setenv("OMICS_DIR", str(HERE / "cache"))
    out = tmp_path / "omics.json.gz"
    build.main(["--drugs", str(HERE / "replay_drugs.txt"), "--pairs", str(HERE / "replay_pairs.txt"),
                "--pts-per-drug", "0", "--out", str(out)])
    assert out.read_bytes() == FIXTURE.read_bytes()


def test_dry_run_counts_uncached_calls_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("OMICS_DIR", str(tmp_path / "empty"))
    out = tmp_path / "omics.json.gz"
    build.main(["--drugs", str(HERE / "replay_drugs.txt"), "--pairs", str(HERE / "replay_pairs.txt"),
                "--pts-per-drug", "0", "--out", str(out), "--dry-run"])
    assert not out.exists()
    f = Fetcher(root=tmp_path / "empty", dry_run=True)
    build.build(f, {"NIRAPARIB": ["thrombocytopenia"], "CLOZAPINE": ["catalepsy", "some unmapped term"]})
    planned = {s: v["not_cached"] for s, v in f.stats.items()}
    assert planned == {"opentargets": 3, "ols": 6, "gtex": 1, "hpo": 3, "mondo": 3}
    assert sum(v["sent"] for v in f.stats.values()) == 0


def test_plan_skips_nonclinical_pts_and_keeps_input_order():
    want, dropped = build.plan(["NIRAPARIB"], [("NIRAPARIB", "anaemia")], {"NIRAPARIB": ["Drug ineffective", "Nausea"]},
                               [], None)
    assert want == {"NIRAPARIB": ["nausea", "anaemia"]}
    assert dropped == {"drug ineffective"}


HPO_THROMBO = {"id": "HP:0001873", "name": "Thrombocytopenia", "synonyms": ["Low platelet count"]}


def test_label_match_wins_and_records_source(tmp_path):
    f = cached(tmp_path, tool("ols_search_efo_terms", {"query": "thrombocytopenia", "rows": 5},
                              {"terms": [{"obo_id": "HP:0001873", "short_form": "HP_0001873",
                                          "label": "Thrombocytopenia"}]}),
               tool("OpenTargets_get_disease_ancestors_parents_by_efoId", {"efoId": "HP_0001873"},
                    {"disease": {"id": "HP_0001873", "ancestors": ["EFO_0000651"]}}))
    assert terms.map_term(f, "Thrombocytopenia", ["Blood"]) == {
        "id": "HP_0001873", "label": "Thrombocytopenia", "match": "label", "source": "ols_efo",
        "ancestors": ["EFO_0000651"], "organs": None}


def test_synonym_match_falls_through_to_hpo(tmp_path):
    f = cached(tmp_path, tool("ols_search_efo_terms", {"query": "low platelet count", "rows": 5},
                              {"terms": [{"short_form": "EFO_0000001", "label": "platelet count"}]}),
               tool("HPO_search_terms", {"query": "low platelet count", "max_results": 5}, [HPO_THROMBO]),
               tool("OpenTargets_get_disease_ancestors_parents_by_efoId", {"efoId": "HP_0001873"},
                    {"disease": {"id": "HP_0001873", "ancestors": []}}))
    rec = terms.map_term(f, "low platelet count", [])
    assert (rec["id"], rec["label"], rec["match"], rec["source"]) == ("HP_0001873", "Thrombocytopenia", "synonym",
                                                                      "hpo")


def test_uk_spelling_is_searched_in_us_form(tmp_path):
    f = cached(tmp_path, tool("ols_search_efo_terms", {"query": "anemia", "rows": 5}, {"terms": []}),
               tool("HPO_search_terms", {"query": "anemia", "max_results": 5},
                    [{"id": "HP:0001903", "name": "Anemia", "synonyms": ["Anaemia"]}]),
               tool("OpenTargets_get_disease_ancestors_parents_by_efoId", {"efoId": "HP_0001903"},
                    {"disease": {"id": "HP_0001903", "ancestors": []}}))
    rec = terms.map_term(f, "anaemia", [])
    assert (rec["id"], rec["match"], rec["source"]) == ("HP_0001903", "label", "hpo")


def test_no_exact_match_keeps_first_hit_and_does_not_roll_up(tmp_path):
    f = cached(tmp_path, tool("ols_search_efo_terms", {"query": "platelet disorder x", "rows": 5},
                              {"terms": [{"short_form": "HP_0001872", "label": "Abnormal platelet count"}]}),
               tool("HPO_search_terms", {"query": "platelet disorder x", "max_results": 5}, [HPO_THROMBO]),
               tool("Mondo_search_disease", {"query": "platelet disorder x", "limit": 5}, []))
    assert terms.map_term(f, "platelet disorder x", ["Blood"]) == {
        "id": None, "label": None, "match": "none", "source": None, "ancestors": None, "organs": None,
        "first_hit": {"id": "HP_0001872", "label": "Abnormal platelet count", "source": "ols_efo"}}


def ot_absent(tid):
    return tool("OpenTargets_get_disease_ancestors_parents_by_efoId", {"efoId": tid},
                {"status": "error", "error": f"{terms.OT_NO_DISEASE} '{tid}'. OpenTargets migrated most disease IDs"})


def test_ancestors_fall_back_to_hpo_walk_then_null_with_error(tmp_path):
    f = cached(tmp_path, ot_absent("HP_0001873"), ot_absent("MONDO_0000001"),
               tool("HPO_get_term_hierarchy", {"term_id": "HP:0001873", "direction": "parents"},
                    [{"id": "HP:0011873", "name": "Abnormal platelet count"}]),
               tool("HPO_get_term_hierarchy", {"term_id": "HP:0011873", "direction": "parents"}, []))
    assert terms.ancestors(f, "HP_0001873") == ["HP_0011873"]
    assert terms.ancestors(f, "MONDO_0000001") is None
    assert f.errors == [{"source": "build", "request": {"ancestors": "MONDO_0000001"}, "error": "no_ancestors"}]


def test_open_targets_not_found_is_cached_as_an_answer_not_an_error(tmp_path, monkeypatch):
    answers = {"OpenTargets_get_disease_ancestors_parents_by_efoId": ot_absent("HP_0000822")[2],
               "HPO_get_term_hierarchy": {"status": "success", "data": []}}
    monkeypatch.setattr(fetch, "_toolu", lambda name, _args: answers[name])
    f = Fetcher(root=tmp_path, gap=0)
    assert terms.ancestors(f, "HP_0000822") == []
    assert f.errors == []
    replay = Fetcher(root=tmp_path, dry_run=True)
    assert terms.ancestors(replay, "HP_0000822") == []
    assert replay.stats == {"opentargets": {"cached": 1, "sent": 0, "not_cached": 0, "failed": 0},
                            "hpo": {"cached": 1, "sent": 0, "not_cached": 0, "failed": 0}}


HP_TERMS = [
    tool("HPO_get_term", {"term_id": "HP:0011875"},
         {"name": "Abnormal platelet morphology", "synonyms": ["Abnormal shape of platelets"]}),
    tool("HPO_get_term", {"term_id": "HP:0001871"},
         {"name": "Abnormality of blood and blood-forming tissues", "synonyms": ["Hematological abnormality"]}),
    tool("HPO_get_term", {"term_id": "HP:0000118"}, {"name": "Phenotypic abnormality",
                                                       "synonyms": ["Organ abnormality"]}),
]


def test_organ_candidates_need_every_word_of_the_tissue_group_name(tmp_path):
    f = cached(tmp_path, *HP_TERMS)
    anc = ["HP_0011875", "HP_0001871", "HP_0000118", "EFO_0000651"]
    assert terms.organs(f, anc, ["Adipose Tissue", "Blood", "Blood Vessel", "Liver"]) == {
        "sites": ["Blood"], "method": "hpo_ancestor_label",
        "evidence": [{"ancestor": "HP_0001871", "word": "blood"}]}
    assert terms.organs(f, anc, ["Liver", "Lung"]) is None
    assert terms.organs(f, [], ["Blood"]) is None


def test_failed_call_is_null_with_error_and_not_cached(tmp_path, monkeypatch):
    def down(*_a, **_k):
        raise RuntimeError("down")
    monkeypatch.setattr(fetch, "_toolu", down)
    monkeypatch.setattr(fetch.time, "sleep", lambda _s: None)
    f = Fetcher(root=tmp_path, gap=0)
    assert layers.gtex(f, "ENSG00000143799", ["Whole_Blood"]) is None
    assert f.errors == [{"source": "gtex", "request": {"tool": "GTEx_get_median_gene_expression", "arguments": {
        "gencode_id": "ENSG00000143799", "dataset_id": "gtex_v10"}}, "error": "RuntimeError: down"}]
    assert f.stats["gtex"] == {"cached": 0, "sent": 3, "not_cached": 0, "failed": 1}
    assert not any(tmp_path.rglob("*.json"))


def test_absent_safety_field_is_null_and_empty_field_is_empty_list(tmp_path):
    f = cached(tmp_path,
               tool("OpenTargets_get_target_safety_profile_by_ensemblID", {"ensemblId": "ENSG_A"},
                    {"target": {"id": "ENSG_A"}}),
               tool("OpenTargets_get_target_safety_profile_by_ensemblID", {"ensemblId": "ENSG_B"},
                    {"target": {"id": "ENSG_B", "safetyLiabilities": []}}))
    assert layers.safety(f, "ENSG_A") is None
    assert layers.safety(f, "ENSG_B") == []


def test_gtex_missing_tissue_is_null_not_zero(tmp_path):
    f = cached(tmp_path, tool("GTEx_get_median_gene_expression", {"gencode_id": "ENSG_A", "dataset_id": "gtex_v10"},
                              [{"median": 1.5, "tissueSiteDetailId": "Liver"}]))
    assert layers.gtex(f, "ENSG_A", ["Liver", "Whole_Blood"]) == {"Liver": 1.5, "Whole_Blood": None}


def dump_entry(ensg, index, size, count, rows, nolit):
    variables = {"id": ensg, "page": {"index": index, "size": size}, "noLit": layers.NO_LITERATURE}
    return ("opentargets", {"graphql": "TargetAssociationDump", "query": layers.Q_ASSOC_DUMP, "variables": variables},
            {"target": {"all": {"count": count, "rows": [{"disease": {"id": d}, "score": s} for d, s in rows]},
                        "noLiterature": {"count": count, "rows": [{"disease": {"id": d}, "score": s}
                                                                  for d, s in nolit]}}})


def test_association_dump_pages_and_scores_literature_only_rows_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(layers, "PAGE", 1)
    f = cached(tmp_path, dump_entry("ENSG_A", 0, 1, 2, [("HP_X", 0.0125)], [("HP_Y", 0.2)]),
               dump_entry("ENSG_A", 1, 1, 2, [("HP_Y", 0.3)], []))
    assert layers.association_dump(f, "ENSG_A") == {"HP_X": (0.0125, 0.0), "HP_Y": (0.3, 0.2)}


def test_pair_assoc_max_over_targets_and_null_when_unknown():
    term = {"id": "HP_X", "ancestors": []}
    dumps = {"A": {"HP_X": (0.0125, 0.0)}, "B": {"HP_X": (0.01, 0.0)}, "C": {}, "D": None}
    assert layers.pair_assoc(term, ["A", "B", "C"], dumps) == {"score": 0.0125, "score_no_literature": 0.0,
                                                               "row_found": True}
    assert layers.pair_assoc(term, ["C"], dumps) == {"score": None, "score_no_literature": None, "row_found": False}
    assert layers.pair_assoc(term, ["A", "D"], dumps) is None
    assert layers.pair_assoc({"id": "HP_X", "ancestors": None}, ["A"], dumps) is None
    assert layers.pair_assoc({"id": None, "ancestors": None}, ["A"], dumps) is None


def test_same_event_id_from_two_sources_merges_into_one_liability():
    raw = [{"event": "confusion", "eventId": "HP_0004372",
            "biosamples": [{"tissueId": "UBERON_0004535"}, {"tissueId": "UBERON_0001017"},
                           {"tissueId": "UBERON_0000949"}],
            "datasource": "Bowes et al. (2012)", "literature": "23197038"},
           {"event": "body weight gain", "datasource": "ClinPGx"},
           {"event": "confusion", "eventId": "HP_0004372",
            "biosamples": [{"tissueId": "UBERON_0001008"}, {"tissueId": "UBERON_0001017"}],
            "datasource": "Lynch et al. (2017)", "literature": ["28216264", "23197038"]}]
    assert layers.merge_liabilities(raw) == [
        {"event": "confusion", "event_id": "HP_0004372",
         "tissue_ids": ["UBERON_0004535", "UBERON_0001017", "UBERON_0000949", "UBERON_0001008"],
         "datasource": "Bowes et al. (2012);Lynch et al. (2017)", "pmid": "23197038;28216264"},
        {"event": "body weight gain", "event_id": None, "tissue_ids": [], "datasource": "ClinPGx", "pmid": None}]


def test_safety_match_marks_term_and_ancestor_relations():
    term = {"id": "HP_0001873", "ancestors": ["HP_0001871"]}
    targets = {"A": {"safety": [{"event_id": "HP_0001871"}, {"event_id": None}, {"event_id": "HP_0001873"}]},
               "B": {"safety": None}}
    assert layers.safety_match(term, ["A", "B"], targets) == [
        {"target": "A", "index": 0, "relation": "ancestor"}, {"target": "A", "index": 2, "relation": "term"}]
    assert layers.safety_match({"id": None, "ancestors": None}, ["A"], targets) is None

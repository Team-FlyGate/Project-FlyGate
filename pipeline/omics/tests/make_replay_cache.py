"""Writes the replay cache that `test_build.py` turns into tests/fixtures/omics_fixture.json.gz without network.

Responses are hand-written in the shape ToolUniverse 1.5.7 and the Open Targets GraphQL returned on 2026-10-26.
Values marked placeholder in tests/fixtures/README.md are placeholders here too. Ancestor labels and synonyms of
HP_0011875, HP_0001871, and HP_0000118 are trimmed copies of the HPO_get_term responses queried on 2026-10-26.

python -m pipeline.omics.tests.make_replay_cache
"""
import pathlib

from pipeline.omics import layers
from pipeline.omics.fetch import cache_path, source_of, write_entry

CACHE = pathlib.Path(__file__).resolve().parent / "cache"
DAY = "2026-10-26"
PARP1, PARP2, DRD2 = "ENSG00000143799", "ENSG00000129484", "ENSG00000149295"


def tool(name, arguments, response):
    return source_of(name), {"tool": name, "arguments": arguments}, response


def dump(ensg, rows, nolit):
    variables = {"id": ensg, "page": {"index": 0, "size": layers.PAGE}, "noLit": layers.NO_LITERATURE}
    return ("opentargets", {"graphql": "TargetAssociationDump", "query": layers.Q_ASSOC_DUMP, "variables": variables},
            {"target": {"id": ensg, "approvedSymbol": None,
                        "all": {"count": len(rows), "rows": [{"disease": {"id": d}, "score": s} for d, s in rows]},
                        "noLiterature": {"count": len(nolit),
                                         "rows": [{"disease": {"id": d}, "score": s} for d, s in nolit]}}})


def moa(action, mechanism, ensg, symbol):
    return {"mechanismOfAction": mechanism, "actionType": action, "targets": [{"id": ensg, "approvedSymbol": symbol}]}


def gtex(ensg, values):
    return tool("GTEx_get_median_gene_expression", {"gencode_id": ensg, "dataset_id": "gtex_v10"},
                [{"median": v, "tissueSiteDetailId": t, "datasetId": "gtex_v10"} for t, v in values.items()])


def search(name, query, response):
    args = {"ols_search_efo_terms": {"query": query, "rows": 5}, "HPO_search_terms": {"query": query, "max_results": 5},
            "Mondo_search_disease": {"query": query, "limit": 5}}[name]
    return tool(name, args, response)


ENTRIES = [
    ("opentargets", {"graphql": "Meta", "query": layers.Q_META, "variables": None},
     {"meta": {"apiVersion": {"x": "25", "y": "9", "z": "0"},
               "dataVersion": {"year": "25", "month": "09", "iteration": None}}}),
    *[("ols", {"get": layers.OLS_ONTOLOGY.format(o)}, {"config": {"version": "placeholder"}})
      for o in ("efo", "hp", "mondo")],
    tool("GTEx_get_tissue_sites", {"dataset_id": "gtex_v10"},
         [{"tissueSiteDetailId": "Whole_Blood", "tissueSite": "Blood"},
          {"tissueSiteDetailId": "Liver", "tissueSite": "Liver"},
          {"tissueSiteDetailId": "Brain_Cortex", "tissueSite": "Brain"}]),
    tool("OpenTargets_get_drug_chembId_by_generic_name", {"drugName": "NIRAPARIB"},
         {"search": {"hits": [{"id": "CHEMBL1094636", "name": "NIRAPARIB"}, {"id": "CHEMBL4650351", "name": "PARPI"},
                              {"id": "CHEMBL3989922", "name": "NIRAPARIB TOSYLATE MONOHYDRATE"}]}}),
    tool("OpenTargets_get_drug_chembId_by_generic_name", {"drugName": "CLOZAPINE"},
         {"search": {"hits": [{"id": "placeholder", "name": "CLOZAPINE"}]}}),
    tool("OpenTargets_get_drug_mechanisms_of_action_by_chemblId", {"chemblId": "CHEMBL1094636"},
         {"drug": {"id": "CHEMBL1094636", "mechanismsOfAction": {"rows": [
             moa("INHIBITOR", "Poly [ADP-ribose] polymerase-1 inhibitor", PARP1, "PARP1"),
             moa("placeholder", "placeholder", PARP2, "PARP2")]}}}),
    tool("OpenTargets_get_drug_mechanisms_of_action_by_chemblId", {"chemblId": "placeholder"},
         {"drug": {"id": "placeholder", "mechanismsOfAction": {"rows": [
             moa("placeholder", "placeholder", DRD2, "DRD2")]}}}),
    tool("DGIdb_get_drug_gene_interactions", {"genes": ["PARP1", "PARP2"]},
         {"genes": {"nodes": [{"name": "PARP1", "interactions": [{"drug": {"name": "NIRAPARIB"}}]}]}}),
    tool("DGIdb_get_drug_gene_interactions", {"genes": ["DRD2"]}, {"genes": {"nodes": []}}),
    tool("OpenTargets_get_target_safety_profile_by_ensemblID", {"ensemblId": PARP1},
         {"target": {"id": PARP1, "approvedSymbol": "PARP1"}}),
    tool("OpenTargets_get_target_safety_profile_by_ensemblID", {"ensemblId": PARP2},
         {"target": {"id": PARP2, "approvedSymbol": "PARP2"}}),
    tool("OpenTargets_get_target_safety_profile_by_ensemblID", {"ensemblId": DRD2},
         {"target": {"id": DRD2, "approvedSymbol": "DRD2", "safetyLiabilities": [
             {"event": "catalepsy", "eventId": "EFO_0009845",
              "biosamples": [{"tissueLabel": "renal", "tissueId": "UBERON_0001008"},
                             {"tissueLabel": "central nervous system", "tissueId": "UBERON_0001017"},
                             {"tissueLabel": "cardiovascular", "tissueId": "UBERON_0004535"},
                             {"tissueLabel": "gastrointestinal", "tissueId": "UBERON_0005409"}],
              "effects": [{"dosing": "acute", "direction": "Inhibition/Decrease/Downregulation"}],
              "datasource": "Lynch et al. (2017)", "literature": "28216264"},
             {"event": "placeholder liability", "datasource": "placeholder"}]}}),
    gtex(PARP1, {"Whole_Blood": 8.5, "Liver": 4.25, "Brain_Cortex": 6.0}),
    gtex(PARP2, {"Whole_Blood": 3.5, "Liver": 2.0, "Brain_Cortex": 1.5}),
    gtex(DRD2, {"Whole_Blood": 0.25, "Liver": 0.5, "Brain_Cortex": 2.75}),
    dump(PARP1, [("HP_0001873", 0.0125)], [("HP_0001873", 0)]),
    dump(PARP2, [], []),
    dump(DRD2, [], []),
    search("ols_search_efo_terms", "thrombocytopenia",
           {"count": 2, "terms": [{"obo_id": "HP:0001873", "short_form": "HP_0001873", "label": "Thrombocytopenia"},
                                  {"obo_id": "EFO:0700038", "short_form": "EFO_0700038",
                                   "label": "autosomal thrombocytopenia with normal platelets"}]}),
    tool("OpenTargets_get_disease_ancestors_parents_by_efoId", {"efoId": "HP_0001873"},
         {"disease": {"id": "HP_0001873", "name": "Thrombocytopenia",
                      "ancestors": ["HP_0011875", "HP_0001871", "HP_0000118", "EFO_0000651"]}}),
    tool("HPO_get_term", {"term_id": "HP:0011875"},
         {"id": "HP:0011875", "name": "Abnormal platelet morphology", "synonyms": ["Abnormal shape of platelets"]}),
    tool("HPO_get_term", {"term_id": "HP:0001871"},
         {"id": "HP:0001871", "name": "Abnormality of blood and blood-forming tissues",
          "synonyms": ["Abnormality of blood and blood-forming tissues", "Abnormality of the haematopoietic system",
                       "Abnormality of the hematopoietic system", "Haematological abnormality",
                       "Hematological abnormality", "Hematologic disease"]}),
    tool("HPO_get_term", {"term_id": "HP:0000118"},
         {"id": "HP:0000118", "name": "Phenotypic abnormality", "synonyms": ["Organ abnormality"]}),
    search("ols_search_efo_terms", "catalepsy",
           {"count": 1, "terms": [{"obo_id": "EFO:0009845", "short_form": "EFO_0009845", "label": "catalepsy"}]}),
    tool("OpenTargets_get_disease_ancestors_parents_by_efoId", {"efoId": "EFO_0009845"},
         {"disease": {"id": "EFO_0009845", "name": "catalepsy", "ancestors": []}}),
    search("ols_search_efo_terms", "some unmapped term", {"count": 0, "terms": []}),
    search("HPO_search_terms", "some unmapped term", []),
    search("Mondo_search_disease", "some unmapped term", []),
]


def main() -> None:
    for source, key, response in ENTRIES:
        write_entry(cache_path(CACHE, source, key), key, DAY, response)
    print(f"{len(ENTRIES)} entries under {CACHE}")


if __name__ == "__main__":
    main()

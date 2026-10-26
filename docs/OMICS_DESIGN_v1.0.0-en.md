# Design of the omics evidence layer for FlyVigilance

Version v1.0.0 · Written 2026-10-26 · Status: awaiting review · Korean original: [OMICS_DESIGN_v1.0.0.md](OMICS_DESIGN_v1.0.0.md)

FlyVigilance scores a drug-reaction pair on three axes today. Was it reported (FAERS disproportionality), is it in the label (openFDA), and is it in the literature (PubMed). This document adds a fourth axis, whether the reaction is biologically plausible. Starting from the drug's mechanism-of-action target genes, it queries public omics databases for target safety liabilities, tissue expression, and target-disease association. The results enter the existing evidence-ID catalog under an `omics:` prefix. The System-2 memo cites them, the critic checks them, and the dashboard shows them in a table. They do not enter the evidence grade or the PV class. The earlier pilot showed why.

## 1. Why now, and why this shape

The pilot of 2026-09-28 ([EVALUATION.md section 7](EVALUATION.md)) used a single Open Targets target-disease association score to separate SIDER label-listed pairs from the rest. It reached AUC 0.559 against a null of 0.532. On the same rows PRR scored 0.570, the ROR lower bound 0.625, IC025 0.638, and chi-square 0.679. 68.4% of rows scored zero, and more than half of the non-zero rows got their score from literature co-mention alone. Only 963 of 3,929 PTs (24.5%) mapped to an ontology term.

Three decisions follow from that result.

1. No single omics score ranks signals. v1 is explanatory evidence. A scoring axis (Role B) enters only after it beats the null on a reference set.
2. The evidence splits into four layers. Beyond the pilot's association score, v1 adds target safety liabilities and GTEx tissue expression, and it marks rows whose only support is literature.
3. PT mapping coverage comes first. Synonym search replaces exact name matching.

The presentation is due 2026-10-29 and the demo runs on flygate.kr on 2026-11-10. v1 holds only what can be measured by the deadline.

## 2. What comes from where

All four layers were queried through ToolUniverse 1.5.7 (`uvx --from tooluniverse==1.5.7 tu run`) on a compute node on 2026-10-26 to confirm the response shapes. Those responses were not cached. The build sends the same queries again and caches them under `$OMICS_DIR`. Tool names are the ToolUniverse registry names.

| Layer | Question | Tool | Fields used | Evidence ID |
|---|---|---|---|---|
| L1 targets | Which genes does the drug act on | `OpenTargets_get_drug_chembId_by_generic_name` then `OpenTargets_get_drug_mechanisms_of_action_by_chemblId`. Cross-checked with `DGIdb_get_drug_gene_interactions` | `targets[].id` (Ensembl), `approvedSymbol`, `actionType`, `mechanismOfAction`, `references[]` | `omics:target:<DRUG>:<SYMBOL>@OT<ver>` |
| L2 target safety | What liabilities are known for perturbing this target | `OpenTargets_get_target_safety_profile_by_ensemblID` | `safetyLiabilities[].event`, `eventId` (HP, EFO, or MONDO), `biosamples[].tissueId` (UBERON), `effects[]`, `datasource`, `literature` (PMID) | `omics:safety:<SYMBOL>:<eventId or slug>@OT<ver>` |
| L3 tissue expression | How much is the target expressed in the tissue where the reaction occurs | `GTEx_get_median_gene_expression` (`dataset_id="gtex_v10"`); tissue list from `GTEx_get_tissue_sites` | `median` (TPM), `tissueSiteDetailId`, `tissueSite`, `ontologyId` (UBERON). 54 detailed tissues, 30 tissue groups | `omics:gtex:<SYMBOL>:<tissueSiteDetailId>@gtex_v10` |
| L4 target-disease association | Is there association evidence between this target and this reaction term | The pilot's Open Targets GraphQL (`associatedDiseases`, with the no-literature alias), ported as is | `score`, `score_no_literature`, `datatypeScores[]` | `omics:assoc:<DRUG>:<termId>@OT<ver>` |
| Term mapping | Which ontology term is this PT | `ols_search_efo_terms`, `HPO_search_terms`, `Mondo_search_disease`, `OpenTargets_get_disease_ancestors_parents_by_efoId`, `HPO_get_term_hierarchy`, `HPO_get_term` | `obo_id` or `id`, `label` or `name`, `synonyms`, `ancestors` | No evidence ID. The `terms` table records source and match kind |

Checked examples. Niraparib is `CHEMBL1094636`, with mechanism-of-action targets PARP1 (`ENSG00000143799`, "Poly [ADP-ribose] polymerase-1 inhibitor") and PARP2 (`ENSG00000129484`). The PARP1 response carried no `safetyLiabilities` field. PARP2 was the same. The build records that as "nothing recorded in Open Targets" and keeps it distinct from zero. DRD2 (`ENSG00000149295`) returns entries with event IDs and tissue IDs, such as "catalepsy" (`EFO_0009845`, four UBERON tissues, source Lynch et al. 2017, PMID 28216264). GTEx v10 returns PARP1 medians in TPM for 54 tissues including Whole_Blood. In OLS, "Thrombocytopenia" resolves to `HP_0001873` as the first hit with an exact label match. `OpenTargets_get_disease_ancestors_parents_by_efoId` gives its ancestors as `HP_0011875`, `HP_0001871`, `HP_0000118`, and `EFO_0000651`.

HPA (`HPA_get_gene_basic_info_by_ensembl_id`) returned `null` for PARP1 tissue-specific nTPM. The proteomics layer (L6) stays out of v1.

## 3. PT mapping rule

MedDRA needs a license, and this repo holds PT names only (`api/_fv/labeltext.py` handles spelling, word order, and the synonym dictionary `EQUIV`, nothing more). Mapping therefore uses public ontology search.

1. Skip PTs where `labeltext.is_nonclinical` is true (for example "drug ineffective").
2. Lowercase the PT and generate the variants from `labeltext.equivalents()` (US spelling, reversed word order, `EQUIV` synonyms).
3. Call `ols_search_efo_terms` (rows 5), `HPO_search_terms` (5), and `Mondo_search_disease` (5) in that order. If any result's `label` or `synonyms` equals one of the variants, case-insensitively, use that term. Record the match kind as `label` or `synonym`.
4. If all three fail, the mapping is `match: none`. The first hit is kept for reference only. Rolling an unmapped PT up to a parent term is not used in v1, because the pilot's concern about mixing disease and phenotype terms on one scale has to be measured first.
5. Fetch the mapped term's ancestors with `OpenTargets_get_disease_ancestors_parents_by_efoId`. If the term is not in the Open Targets disease index, walk `HPO_get_term_hierarchy` (`direction: "parents"`) to the root for HP terms. If neither works, store `ancestors: null` with an error. L4 is then `null` as well.

Tissue expression (L3) needs the organ where the PT occurs. That value comes from the ontology, not from a model judgment.

- Fetch the label and synonyms of each HP term among the mapped term's ancestors with `HPO_get_term` (the ancestor query returns IDs only). In HPO, the direct children of `HP_0000118` (Phenotypic abnormality) are the organ-system branches. `HP_0001871`, for example, is labeled "Abnormality of blood and blood-forming tissues" with the synonym "Hematological abnormality" (queried 2026-10-26).
- If a word in an ancestor's label or synonyms matches, case-insensitively, a word in one of the 30 tissue-group names returned by `GTEx_get_tissue_sites` (`tissueSite`: Blood, Liver, Brain, and so on), that group becomes a tissue candidate. In the example above, "blood" matches and Blood becomes the candidate. The rule is one word-set intersection, with no exception table.
- If no group matches, `organs` is `null`. L3 then reports the top 5 of the 54 tissues by TPM without a candidate filter.
- The method is recorded as `hpo_ancestor_label`, together with which ancestor and which word matched. After the build, the README records the share of PTs that got a tissue candidate.

The rule is coarse, but every step comes from a query result and a person can retrace it. When the MedDRA SOC hierarchy becomes available, the rule is replaced by a SOC table (section 7).

## 4. Data shape

The output is one file, `api/_data/omics.json.gz`. Facts live once in three tables, `drugs`, `targets`, and `terms`. The `pairs` table holds only keys into those tables and values that are defined by the pair alone. Evidence items are built at request time by a pure function `items(pair)` in `api/_fv/omics.py` that reads the tables. The L1, L2, and L3 sentences of a target are therefore not repeated across 80 pairs, and the file size scales with the number of drugs, targets, and terms.

```json
{
  "asof": "2026-10-27",
  "versions": {"tooluniverse": "1.5.7", "opentargets": "<recorded from meta>", "gtex": "gtex_v10",
               "ols_efo": "<recorded at query time>", "hpo": "<recorded at query time>", "mondo": "<recorded at query time>"},
  "drugs": {
    "NIRAPARIB": {"chembl_id": "CHEMBL1094636", "match": "name_exact",
                  "targets": ["ENSG00000143799", "ENSG00000129484"]}
  },
  "targets": {
    "ENSG00000143799": {
      "symbol": "PARP1",
      "moa": [{"drug": "NIRAPARIB", "action": "INHIBITOR",
               "mechanism": "Poly [ADP-ribose] polymerase-1 inhibitor", "dgidb": true}],
      "safety": null,
      "gtex": {"Whole_Blood": 0.0, "Liver": 0.0}
    }
  },
  "terms": {
    "thrombocytopenia": {"id": "HP_0001873", "label": "Thrombocytopenia", "match": "label", "source": "ols_efo",
                         "ancestors": ["HP_0011875", "HP_0001871", "HP_0000118", "EFO_0000651"],
                         "organs": {"sites": ["Blood"], "method": "hpo_ancestor_label",
                                    "evidence": [{"ancestor": "HP_0001871", "word": "blood"}]}}
  },
  "pairs": {
    "NIRAPARIB|thrombocytopenia": {
      "term": "thrombocytopenia",
      "safety_match": [],
      "assoc": {"score": 0.0125, "score_no_literature": 0.0, "row_found": true}
    }
  },
  "errors": []
}
```

In this example the real query values are the CHEMBL ID, the Ensembl IDs, the mechanism string, the ancestor list, and the association score 0.0125 (pilot). The `gtex` values 0.0 and `organs` are placeholders. `safety: null` means the field was absent; `[]` means the field was present and empty.

Rules.

- The pair key is `<DRUG>|<pt lowercase>`, where DRUG is the `signals.json.gz` key as is (`drug.upper()`, with `\` kept in combination products). The `+` substitution of `evidence.id_drug` is used only inside evidence IDs. `omics.pair(drug, pt)` normalizes its input with `upper()` and `lower()` only.
- `pairs[].safety_match` lists the indexes of the target's safety liabilities whose `eventId` equals the term ID (`term`) or is one of the term's ancestors (`ancestor`). This does not roll up the PT mapping. It records how an already mapped term relates to an event ID. Hierarchy comparison between tissue IDs is not done in v1.
- `items(pair)` builds evidence items shaped `{"id", "layer", "what", "n"}`. L1 gives one per target. L2 gives one per safety liability per target, with a `match` field of `term`, `ancestor`, or `none`. L3 gives one per detailed tissue inside the tissue candidates (top 5 by TPM when there are no candidates). L4 gives one. The L3 `n` holds the median TPM and the rank among 54 tissues. No "expressed" verdict is attached, because a threshold cannot be set without measurement.
- L4 emits the pilot's two scores. `what` says "literature co-mention only" only when `score > 0` and `score_no_literature == 0`.
- When the mapping is `none`, `safety_match` and `assoc` are `null`. `items` returns all of L1, all of L2 (`match: none`), and the top 5 of L3, and no L4.
- The set that enters the System-2 memo is cut separately by `items_for_memo(pair)`: at most 5 L1 items, only the L2 items whose `match` is `term` or `ancestor`, at most 5 L3 items inside the tissue candidates, and one L4 item. The dashboard and the CLI show all of `items`. This keeps a drug with 51 targets, such as metformin, from flooding the Nemotron prompt.
- There is no pair-level verdict (supported, partial, none). Only per-layer counts. A verdict rule is set after the Role B measurement.
- A failed query yields `null` and an entry in `errors[]`. Zero is never substituted.

`what` sentences are written in English and state facts independent of the pair. The `what` of a given ID is therefore identical in every bundle, and duplicates merge safely in the `ids` set of `evidence.bundle`. Every `what` ends with "Population-level mechanistic context; not evidence that the drug caused this reaction in this case."

Critic tier 2 accepts a number when `abs(x - y) <= max(0.011, abs(y) * 0.011)` (`api/_fv/assess.py:92`). L4 scores such as 0.0125 and 0.0 fall inside that tolerance, so tier 2 cannot tell them apart. v1 records this limit and leaves it. The memo rarely quotes L4 numbers, and changing the tolerance would require rerunning the existing critic measurement (31 of 31 in `docs/EVALUATION.md`).

## 5. Where it attaches

| Place | Change | File |
|---|---|---|
| Loader | Cached `_omics()`, `pair(drug, pt)`, `drug_pairs(drug)`, `drugs()`, `items(pair)`, `items_for_memo(pair)`. Empty structure when the file is missing | new `api/_fv/omics.py` |
| Evidence bundle | For each reaction in the list `pts` that `bundle()` already builds (`evidence.py:246`), append `items_for_memo` to `catalog` and include the IDs in `ids`. The module docstring gains the four `omics:` prefixes | `api/_fv/evidence.py:242-296` |
| System-2 memo | R14 added to `OVERCLAIM_RULES` | `api/_fv/assess.py:17-31` |
| Other places that list the rules | The rule list, the "13 rules" wording, and the critic skill doc | `web/src/pages/Skills.tsx:13-22`, `web/src/lib/glossary.ts:377,814`, `skills/pv-critic/SKILL.md:45,48` |
| Grade | `grade.py` unchanged. The `/api/grade` response gains `omics: {"count": n, "mapping": ...}`. One Korean line is added to `gaps` ("오믹스 근거는 등급에 반영하지 않음") with its English counterpart in `GAP_EN` | `api/index.py:145-161`, `web/src/components/GradeCard.tsx:43-57` |
| API | `GET /api/omics?drug=&pt=` (one pair), `GET /api/omics?drug=` (all pairs of a drug), `GET /api/omics/drugs` (drug list). Query parameters instead of path variables because 13 PTs contain `/`. 404 when absent. Add an `omics` key to `LIMIT`. Update the endpoint list in the docstring | `api/index.py:39-45`, `index.py:1-14` |
| CLI | `flygate omics <DRUG> "<PT>"`. Output is all of `items` plus `evidence_ids`. For a drug or pair outside the extract it prints `{"found": false, "evidence_ids": []}` with a reason and exits 0. Update `ALLOWED`, `HELP`, the `SYSTEM` command list, the banner tool count (`'7 tools'` to `'8 tools'`), and `TOOLS.md` | `agent/flygate.py`, `agent/chat.py:18-56`, `agent/banner.py:82`, `agent/workspace/TOOLS.md` |
| Dashboard | `/#/omics` page. Pick a drug from `/api/omics/drugs`, list its pairs, show a per-layer table. `GradeCard` shows a link "omics evidence: n items" from `omics.count` in the `/api/grade` response | `web/src/pages/Omics.tsx`, `web/src/App.tsx:49-58`, `web/src/components/GradeCard.tsx` |
| Policy | Unchanged. Queries run only at build time; the runtime only reads the extract file | `agent/policy/flygate.yaml` |
| Skill | `skills/pv-omics-evidence/SKILL.md` with every required frontmatter field from `skills/README.md:26` (`name`, `title`, `version`, `description`, `license`, `compatibility`, `metadata.author/domain/tags/layer/model`). The skill-card is generated with the NVIDIA `skill-card-generator` scripts when they are available, otherwise the PR marks it as pending. Update the skill count in the README (11 to 12) and rerun `pipeline/build_skills.py` | `skills/`, `skills/README.md:3-4,10` |

R14 wording.

> R14: Mechanistic evidence (target safety liabilities, tissue expression, target-disease association) shows biological plausibility at the population level. It never establishes that the drug caused the reaction in this case, and absence of mechanistic evidence is not evidence against the association.

Critic tier 1 (evidence ID exists) and tier 2 (number tolerance) apply to `omics:` items unchanged. Tier 3 reads R14 from the rule list.

## 6. Build

Code lives in `pipeline/omics/`. The pilot's `scripts/omics_plausibility.py` (old repo `korea-agentic-hackathon-2026`, branch `omics-plausibility`) contributes its `Fetcher` (sha1 cache, retries, dry run) and its batched reference-set queries. Each host gets the same 0.2 s spacing as `evidence._Spacer`.

| File | Role |
|---|---|
| `fetch.py` | Wraps the ToolUniverse SDK (`ToolUniverse().run_one_function`) and Open Targets GraphQL under one cache rule. Cache path is `$OMICS_DIR/<source>/<sha1>.json` |
| `terms.py` | PT mapping and tissue candidates from section 3 |
| `layers.py` | L1 to L4 queries |
| `build.py` | `--drugs <file>`, `--pairs <file>`, `--pts-per-drug 80`, `--out api/_data/omics.json.gz`, `--dry-run`, `--limit N`. Prints a coverage table at the end |
| `README.md` | How to run, and the recorded versions |

The build runs on a compute node from the repo root. ToolUniverse is a build dependency and does not enter `requirements.txt` or `api/`. `build.py` puts `api/` on `sys.path`, as `agent/flygate.py` does, to use `labeltext`.

```bash
export OMICS_DIR=/data/hps/assoc/private/rsc/user/ybae/tmp/omics-cache
export UV_CACHE_DIR=/data/hps/assoc/private/rsc/user/ybae/.cache/uv
cd /data/hps/assoc/private/rsc/user/ybae/RSC/Project-FlyGate
srun -A rsc -p cpu-core -c 2 --mem=15000M -t 06:00:00 \
  uv run --no-project --with tooluniverse==1.5.7 python -m pipeline.omics.build \
    --drugs pipeline/omics/drugs_v1.txt --pairs pipeline/omics/pairs_v1.txt \
    --out api/_data/omics.json.gz
```

The drug set `drugs_v1.txt` is the union of the 31 SIDER pilot drugs, the 11 SignalLab presets, the 3 CLI watchlist drugs, the 9 Time Machine drugs, and the 224 primary-suspect drugs of the 440 demo cases. Pairs are the union of three sources: the top 80 PTs per drug from `signals.json.gz`, the top 3 reactions of each demo case with its primary-suspect drug, and the watchlist and Time Machine pairs listed in `pairs_v1.txt`. The last two are needed because 3 of the 10 watchlist pairs and 5 of the 9 Time Machine pairs fall outside the top 80. Any other drug or pair gets a 404 from the API and a "not in the extract" message on screen.

Call counts are measured with `--dry-run` before the build. Roughly, each PT costs 3 ontology searches and 1 ancestor query, each target costs 1 safety, 1 GTEx, and 1 association-list query, and each drug costs 1 ID, 1 mechanism, and 1 DGIdb query. At 0.2 s spacing, 5,000 PTs take about 50 minutes for the searches alone. After the build, the README records the drug count, target count, PT count, mapping rate, tissue-candidate rate, call count, and failure count.

## 7. Out of v1, and next steps

| Item | Status | Condition |
|---|---|---|
| Role B: omics score in the grade | Deferred | Measure per-layer AUC and null on the 64,796 pairs of `pilot_sider_2026-09-28.json.gz`; include only layers that beat the disproportionality metrics. Then confirm on OMOP and EU-ADR |
| MedDRA SOC hierarchy | Deferred | If the team has an MSSO subscription, a PT to SOC table replaces the tissue-candidate rule in section 3. The source files never enter the repo |
| UMLS cross-references | Deferred | After a UTS API key is obtained, check the usage restriction on the MedDRA vocabulary. `umls_search_concepts` opens only with `UMLS_API_KEY` |
| MedDRA cross-references inside Mondo | Needs measurement | The pilot found no MedDRA cross-references in the EFO, MONDO, and HP responses from Open Targets (EVALUATION section 7). Mondo's own API (`Mondo_search_disease`) returned `xref` entries such as `MedDRA:10053176` (cyclic neutropenia). Count how many PTs carry one |
| Parent-term roll-up | Deferred | Measure the score-scale difference between disease and phenotype terms first |
| L5 phenotype to genes (HPO) | Deferred | Intersect `HPO_get_genes_by_phenotype` with the target set |
| L6 proteomics (HPA) | Deferred | Check whether `HPA_get_gene_tsv_data_by_ensembl_id` returns tissue nTPM |
| Critic tier-2 tolerance floor 0.011 | Deferred | Separating small L4 scores needs a new tolerance rule and a rerun of the critic measurement |
| Fly orthologs | Not included | The connectome screen is a metaphor, not clinical evidence |
| Individual-case causality | Not included | R14 |

## 8. Verification

- `tests/test_omics.py`: the loader returns an empty structure when the file is missing, `pair` lookup and 404, evidence ID format (four prefixes), the cut rules of `items` and `items_for_memo`, catalog merge in `bundle` (network functions patched as in `test_label_facts.py`), R14 present in `OVERCLAIM_RULES`, and `flygate omics` returning `found: false` for an unknown drug.
- Add `omics` to the subcommand set in `tests/test_agent.py:130-133`.
- Change `'7 tools'` to `'8 tools'` in `tests/test_chat.py:74`. `test_direct_slash_tools` uses a stub runner and never executes the new command, so `test_omics.py` calls the CLI directly.
- `pipeline/omics/tests/`: replay the cache without network to test the mapping rule, the tissue-candidate rule, and item construction (as the pilot's `tests/test_omics_plausibility.py` did).
- After the build, check the real artifact: the niraparib-thrombocytopenia pair shows `safety: null` for both PARP1 and PARP2 and an L4 no-literature score of 0 (the honest negative). The second demo pair is chosen from the data.
- Each unit of work ends with `.venv/bin/python -m pytest -q tests` passing.

## 9. Sources

- ToolUniverse 1.5.7. Tool names and parameters confirmed with `tu info` on 2026-10-26. 646 tools registered without keys, 2,719 loaded by the SDK.
- Open Targets Platform via the `OpenTargets_*` tools. The data version is recorded per build from `meta`.
- GTEx v10 via `GTEx_get_tissue_sites` (54 detailed tissues, 30 groups, UBERON IDs) and `GTEx_get_median_gene_expression`.
- OLS v4 (EFO), HPO (JAX), Mondo via their search tools.
- Pilot: old repo `docs/notes/omics-plausibility-2026-09-28.md`, results `eval/results/omics_plausibility_refset_2026-09-28.json.gz`, reference set `eval/refsets/pilot_sider_2026-09-28.json.gz` (SIDER 4.1, MedDRA 16.1 PT names, 31 drugs, 64,796 pairs).
- This repo: `api/_fv/evidence.py`, `assess.py`, `grade.py`, `labeltext.py`, `api/index.py`, `agent/flygate.py`, `agent/chat.py`, `agent/banner.py`, `web/src/pages/SignalLab.tsx`, `web/src/components/GradeCard.tsx`, `tests/test_agent.py`, `tests/test_chat.py`.

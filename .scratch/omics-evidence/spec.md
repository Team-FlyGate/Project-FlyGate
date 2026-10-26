# Spec: omics evidence layer for FlyVigilance (v1)

Status: ready-for-agent · Branch: `feat/omics-evidence` · Design: `docs/OMICS_DESIGN_v1.0.0.md` (Korean), `docs/OMICS_DESIGN_v1.0.0-en.md` · Deadline: presentation 2026-10-29, demo on flygate.kr 2026-11-10

## Problem statement

A safety reviewer using FlyVigilance sees three kinds of evidence for a drug-reaction pair: FAERS disproportionality, label wording, and PubMed reading. None of them says whether the reaction is biologically plausible given what the drug does. The reviewer has to look that up by hand in Open Targets, GTEx, and the ontologies, and the System-2 memo cannot cite it because it is not in the evidence catalog. A prior pilot tried to turn mechanistic plausibility into one score and found it ranks signals worse than PRR, so a score is not what the reviewer needs.

## Solution

Add a fourth evidence class, `omics:`, built offline from public databases and shipped as one compressed extract. For each drug-reaction pair in the extract, the reviewer sees four layers: the drug's mechanism-of-action targets, the known safety liabilities of those targets, the targets' expression in the tissue where the reaction occurs, and the target-disease association score with its literature-only flag. Every item has an evidence ID the System-2 memo can cite and the critic can check. A new critic rule R14 stops the memo from turning plausibility into case causality. The grade and PV class do not change.

## User stories

1. As a safety reviewer, I want to open a drug-reaction pair and see which genes the drug acts on, so that I can reason about mechanism without leaving the dashboard.
2. As a safety reviewer, I want to see the known safety liabilities of each target with their source and PMID, so that I can judge whether the reaction is an on-target effect.
3. As a safety reviewer, I want liabilities that match the reaction term, or one of its ancestors, highlighted apart from the rest, so that I do not have to read every liability of a 51-target drug.
4. As a safety reviewer, I want each target's GTEx expression in the tissue where the reaction occurs, with its rank among 54 tissues, so that I can see whether the target is even present there.
5. As a safety reviewer, I want to see the target-disease association score and whether it rests on literature co-mention alone, so that I do not mistake "already reported" for "biologically supported".
6. As a safety reviewer, I want every omics item to carry an evidence ID in the same style as `faers:`, `label:`, and `pubmed:` IDs, so that I can trace any claim in the memo back to a query.
7. As a safety reviewer, I want the memo to say "biologically plausible at the population level" and never "caused this reaction", so that mechanistic context is not misread as causality.
8. As a safety reviewer, I want an honest negative, such as niraparib-thrombocytopenia with no recorded liabilities and a zero no-literature score, to display as "nothing recorded" rather than as a reassuring zero, so that absence of data is not read as safety.
9. As a safety reviewer, I want the grade card to show how many omics items exist for the pair and link to them, so that I know the evidence is there without the grade itself changing.
10. As a safety reviewer, I want to know when a reaction term could not be mapped to an ontology, so that I understand why layers L2, L3, and L4 are empty.
11. As a safety reviewer, I want to know how the organ for tissue expression was chosen (which HPO ancestor, which word), so that I can disagree with it.
12. As a pharmacist on the team, I want the organ mapping and the term mapping to come from ontology queries only, never from a language model's memory, so that every biological statement can be cited.
13. As an agent operator, I want `flygate omics <DRUG> "<PT>"` to print the same items as the API with `evidence_ids`, so that the OpenClaw agent can use omics evidence through its existing single tool.
14. As an agent operator, I want the CLI to say `found: false` with a reason for a drug or pair outside the extract and exit 0, so that the agent loop does not crash on an unknown drug.
15. As the chat agent, I want `omics` in the allowed command set, help text, and banner, so that a reviewer can type `/omics` in `flygate chat`.
16. As the System-2 assessor, I want only a capped set of omics items per reaction in my prompt, so that a drug with many targets does not push the FAERS and label evidence out of the 100 s budget.
17. As the critic, I want R14 in the rule list I judge against, so that I can return a claim that converts plausibility into causality.
18. As the critic, I want omics numbers in the memo to be checked against the bundle like every other number, so that no omics value is invented.
19. As a dashboard visitor, I want a page that lists the drugs in the extract, their pairs, and a per-layer table, so that I can browse omics evidence without knowing drug names in advance.
20. As a dashboard visitor, I want the English view of the grade card to translate the new gap line, so that the English screen has no Korean leftovers.
21. As a dashboard visitor, I want the skills page and the glossary to say 14 rules, not 13, so that the documentation matches the critic.
22. As a hackathon judge, I want a skill `pv-omics-evidence` with the same frontmatter as the other 11 FlyVigilance skills, so that the omics layer appears in the skill catalog and on the skills screen.
23. As a maintainer, I want the build to run on a compute node from one command with pinned ToolUniverse, so that the extract can be regenerated after the hackathon.
24. As a maintainer, I want every HTTP response cached by request hash and replayable without network, so that tests do not need keys and reruns cost nothing.
25. As a maintainer, I want the build to print coverage numbers (drugs, targets, PTs, mapping rate, organ-candidate rate, calls, failures), so that the README states measured numbers, not guesses.
26. As a maintainer, I want a `--dry-run` that counts calls before the real run, so that I know the wall-clock cost before I submit the job.
27. As a maintainer, I want nonclinical PTs skipped, so that the build does not spend calls on "drug ineffective".
28. As a maintainer, I want the extract normalized (facts once per drug, target, and term), so that the file stays small enough for a Vercel cold start.
29. As a maintainer, I want pairs outside the top 80 PTs (watchlist, Time Machine, demo cases) included by an explicit pair list, so that every pair the dashboard shows has omics items.
30. As a maintainer, I want the Vercel API to read the extract only and never import ToolUniverse, so that the deploy stays inside its size and time limits.
31. As a maintainer, I want the OpenShell network policy unchanged, so that the agent sandbox does not gain new hosts.
32. As a reviewer of the PR, I want all tests to pass offline, so that CI does not depend on Open Targets or GTEx uptime.
33. As a future contributor, I want the deferred items (Role B scoring, MedDRA SOC, UMLS, L5, L6, parent roll-up) listed with their conditions, so that I know what was cut and why.
34. As a presenter, I want one positive demo pair chosen from the data and one honest negative, so that the slides show the layer working both ways.

## Implementation decisions

- Four layers, L1 targets, L2 target safety liabilities, L3 GTEx tissue expression, L4 target-disease association. Each has its own evidence-ID prefix: `omics:target`, `omics:safety`, `omics:gtex`, `omics:assoc`. Term mapping has no ID; its provenance lives in the `terms` table.
- Data sources are queried only at build time through ToolUniverse 1.5.7 (pinned) and the pilot's Open Targets GraphQL for L4. Runtime never imports ToolUniverse.
- PT mapping: skip nonclinical PTs; generate spelling, word-order, and `EQUIV` variants; search OLS (EFO), HPO, Mondo; accept a hit only on exact label or synonym match; no parent roll-up.
- Organ candidates for L3: labels and synonyms of the mapped term's HP ancestors, word-matched against the 30 GTEx tissue-group names. No model judgment, no exception table. No match means `organs: null` and L3 shows the top 5 tissues by TPM.
- Extract shape: `asof`, `versions`, `drugs`, `targets`, `terms`, `pairs`, `errors`. Pair key is `<DRUG>|<pt lowercase>` with DRUG in `signals.json.gz` form. `pairs` holds only `term`, `safety_match` (indexes with `term` or `ancestor` relation), and `assoc`.
- Evidence items are composed at request time by a pure function from the tables. `items` returns everything for dashboard and CLI; `items_for_memo` caps to 5 L1, matched L2 only, 5 L3 inside candidates, 1 L4.
- `what` text is English, pair-independent, and ends with the fixed population-level sentence. A missing upstream field is `null`, never 0.
- Evidence bundle appends `items_for_memo` for each reaction it already selected. Critic tiers 1 and 2 apply unchanged; tier 3 gains R14.
- API: query-parameter routes `/api/omics?drug=&pt=`, `/api/omics?drug=`, `/api/omics/drugs`; 404 when absent; rate-limit key `omics`. `/api/grade` response gains `omics: {count, mapping}` without touching the grade module.
- CLI: `flygate omics <DRUG> "<PT>"`; `found: false` with reason and exit 0 when absent; `ALLOWED`, help, system prompt, banner count (7 to 8), and `TOOLS.md` updated.
- Web: hash page `/#/omics` in the FlyVigilance group; drug picker from `/api/omics/drugs`; per-layer table; GradeCard shows the omics count; `GAP_EN` gains the new gap line; rule lists and "13 rules" strings say 14.
- Skill: `pv-omics-evidence` with all required frontmatter fields; skill-card generated with the NVIDIA generator when available, otherwise marked pending; README skill counts updated; `build_skills.py` rerun.
- Build drug set: SIDER pilot 31, SignalLab presets 11, CLI watchlist 3, Time Machine 9, 224 primary-suspect drugs of the demo cases. Pair set: top 80 PTs per drug, demo-case top-3 reactions, and an explicit pair list.
- Grade, PV class, and the OpenShell policy do not change.

## Testing decisions

- A good test calls the code the way its users do and asserts a literal expected value from a fixture. No test asserts on internal helper calls.
- Seam 1, the extract. A small fixture extract (two drugs, a handful of terms, one honest negative) built from cached responses. The loader, item composition, memo cap, API routes, CLI output, bundle catalog merge, and R14 presence are all tested through it with `TestClient` and the CLI entry point, offline, following the existing `test_discovery_api.py` and `test_label_facts.py` patterns (patch module-level `DATA`, clear the lru cache, patch network functions).
- Seam 2, the build. Cache replay without network reproduces the fixture extract byte for byte, following the pilot's `test_omics_plausibility.py` approach. Mapping rule, organ-candidate rule, and `null`-not-zero behavior are tested here.
- Existing tests that enumerate subcommands and the banner tool count are updated, not bypassed.
- Full suite `.venv/bin/python -m pytest -q tests` passes after every ticket.

## Out of scope

- Any omics score in the grade or PV class (Role B). Deferred until it beats the null on the SIDER pilot reference set.
- MedDRA SOC hierarchy and UMLS cross-references (license and key not available).
- Parent-term roll-up of unmapped PTs.
- L5 phenotype-to-gene (HPO) and L6 proteomics (HPA).
- Fly ortholog lookups. The connectome screen stays a metaphor.
- Changing the critic tier-2 tolerance floor.
- Web test runner setup.
- Individual-case causality statements of any kind.

## Further notes

- Checked tool responses on 2026-10-26: PARP1 and PARP2 responses carry no `safetyLiabilities` field; DRD2 does, with event IDs, UBERON tissue IDs, and PMIDs; GTEx v10 returns 54 tissues with UBERON IDs; OLS resolves "Thrombocytopenia" to `HP_0001873`; `HPO_get_term` labels `HP_0001871` "Abnormality of blood and blood-forming tissues", which word-matches GTEx "Blood".
- The critic tier-2 tolerance has an absolute floor of 0.011, so small L4 scores are not distinguishable by tier 2. Recorded as a known limit.
- Mondo's own API returned MedDRA cross-reference codes for some terms. Coverage is unmeasured and may become a license-free mapping path later.

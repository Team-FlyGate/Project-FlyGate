This card was written by hand from the pv-signal-memory card layout. It is pending a run of the NVIDIA skill-card-generator scripts (discover_assets.py, render_card.py, validate_submission.py), which were not available in this environment. <br>

## Description: <br>
Use when a drug-reaction pair needs mechanistic plausibility context: the drug's mechanism-of-action targets, the safety liabilities recorded for those targets, their GTEx tissue expression in the organ where the reaction occurs, and the Open Targets target-disease association score, each returned as a citable omics: evidence ID read from an offline extract. The output is explanatory population-level context only. <br>

This skill is for research and development only. <br>

## Third-Party Community Consideration
This skill is not owned or developed by NVIDIA. This skill has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [Team FlyGate Agent Card](https://github.com/Team-FlyGate/Project-FlyGate). <br>

### License/Terms of Use: <br>
Apache 2.0 <br>
## Use Case: <br>
Pharmacovigilance reviewers and System-2 assessors who need the mechanistic context of a drug-reaction pair (targets, target safety liabilities, tissue expression, target-disease association) as evidence IDs a memo may cite, without treating it as a causality verdict or a grade input. <br>

### Deployment Geography for Use: <br>
Global <br>

## Requirements / Dependencies: <br>
**Requires API Key or External Credential:** [No] <br>
**Credential Type(s):** [None] <br>  

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. See skill body for more details. <br>

## Known Risks and Mitigations: <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>
Risk: Mechanistic evidence, or its absence, could be read as individual-case causality or as evidence against an association. <br>
Mitigation: Every item ends with a population-level disclaimer, missing data is null rather than zero, the grade ignores omics, and critic rule R14 flags overclaims. <br>

## Reference(s): <br>
- [Omics evidence module](../../api/_fv/omics.py) <br>
- [Evidence bundle](../../api/_fv/evidence.py) <br>
- [Overclaim rules (R14)](../../api/_fv/assess.py) <br>
- [Omics evidence layer design v1.0.0](../../docs/OMICS_DESIGN_v1.0.0-en.md) <br>


## Skill Output: <br>
**Output Type(s):** [Analysis] <br>
**Output Format:** [JSON (pair record, items with id, layer, what, n, and match for L2; memo items; evidence IDs)] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Values are read from an offline extract built from public databases; no model and no network call at runtime; missing values stay null] <br>

## Evaluation Tasks: <br>
Offline unit tests on the fixture extract tests/fixtures/omics_fixture.json.gz: tests/test_omics.py, tests/test_omics_api.py and tests/test_omics_bundle.py, plus 5 tasks in evals/evals.json. <br>

## Skill Version(s): <br>
1.0.0 (source: frontmatter) <br>

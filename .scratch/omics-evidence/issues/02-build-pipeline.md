# 02: Build pipeline that produces the extract from public databases

**What to build:** A maintainer runs one command on a compute node with a drug list and a pair list and gets `api/_data/omics.json.gz` in the ticket-01 schema, plus a printed coverage table. Every HTTP response is cached by request hash under `$OMICS_DIR`, and a replay run without network reproduces the fixture extract from ticket 01 byte for byte. The pipeline ports the pilot's fetcher, maps PTs through OLS, HPO, and Mondo with exact label or synonym matching, derives organ candidates from HP ancestor labels word-matched to GTEx tissue groups, and fills L1 to L4.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `python -m pipeline.omics.build --drugs ... --pairs ... --out ...` runs from the repo root with pinned ToolUniverse and does not import anything from the runtime `api/` beyond `labeltext`
- [ ] `--dry-run` prints the planned call count per host without network
- [ ] Nonclinical PTs are skipped; variants come from `labeltext.equivalents()`
- [ ] Term mapping records `match` in `label`, `synonym`, `none`, the source, and the first hit for reference; no parent roll-up
- [ ] Ancestors come from Open Targets, then HPO parents walk, then `null` with an error entry
- [ ] Organ candidates record method `hpo_ancestor_label` with the matching ancestor and word; no match gives `organs: null`
- [ ] L2 stores the full liability list per target, `null` when the field is absent; `safety_match` lists `term` and `ancestor` relations per pair
- [ ] L3 stores GTEx v10 median TPM for all 54 tissues per target
- [ ] L4 stores both pilot scores and `row_found`; literature-only flag only when score > 0 and no-literature score == 0
- [ ] Each host gets 0.2 s spacing; failures are `null` plus an `errors[]` entry, never 0
- [ ] Coverage table prints drugs, targets, PTs, mapping rate, organ-candidate rate, calls, failures, and the versions block records Open Targets `meta`
- [ ] Cache replay test reproduces the ticket-01 fixture without network
- [ ] `pipeline/omics/README.md` documents the command and the recorded numbers

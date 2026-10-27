# pipeline/omics

This pipeline builds `api/_data/omics.json.gz`, the omics evidence extract that `api/_fv/omics.py` reads at runtime. The schema, the PT mapping rule, and the drug and pair sets are in `docs/OMICS_DESIGN_v1.0.0-en.md` sections 3, 4, and 6. The runtime never queries these databases. Only this build does.

| File | Role |
|---|---|
| `fetch.py` | One cache rule for ToolUniverse SDK calls and the Open Targets GraphQL endpoint, with 0.2 s spacing per host and 3 attempts per request |
| `terms.py` | PT to ontology term mapping (OLS EFO, HPO, Mondo), ancestors, and organ candidates |
| `layers.py` | L1 targets, L2 safety liabilities, L3 GTEx v10 medians, L4 association scores, and the version queries |
| `build.py` | The command. It prints a coverage table at the end |
| `lists.py` | Writes `drugs_v1.txt` and `pairs_v1.txt` from their sources |
| `tests/` | Offline tests and the replay cache that reproduces `tests/fixtures/omics_fixture.json.gz` |

## Run

Run the build on a compute node from the repo root. ToolUniverse 1.5.7 needs Python 3.10 or later, and the system Python and the repo `.venv` are 3.9, so the command asks uv for 3.12. ToolUniverse is a build dependency only. It is not in `requirements.txt`, and nothing under `api/` imports it. The build imports `labeltext` from `api/_fv` and nothing else from `api/`.

```bash
export OMICS_DIR=/data/hps/assoc/private/rsc/user/ybae/tmp/omics-cache
export UV_CACHE_DIR=/data/hps/assoc/private/rsc/user/ybae/.cache/uv
export TMPDIR=/data/hps/assoc/private/rsc/user/ybae/tmp
cd /data/hps/assoc/private/rsc/user/ybae/RSC/Project-FlyGate
srun -A rsc -p cpu-core -c 2 --mem=15000M -t 06:00:00 \
  uv run --no-project --python 3.12 --with tooluniverse==1.5.7 python -m pipeline.omics.build \
    --drugs pipeline/omics/drugs_v1.txt --pairs pipeline/omics/pairs_v1.txt --cases \
    --out api/_data/omics.json.gz
```

| Flag | Meaning |
|---|---|
| `--drugs` | One drug per line, in the `signals.json.gz` key form. Lines starting with `#` are skipped |
| `--pairs` | `DRUG<TAB>pt` per line, added to the drug's PTs |
| `--pts-per-drug 80` | Top N PTs per drug from `signals.json.gz` |
| `--cases` | Adds each demo case's primary-suspect drug with its top 3 reactions, chosen the way `evidence.bundle` chooses them |
| `--dry-run` | Reads the cache only, sends nothing, writes nothing, and prints the calls that are not cached yet |
| `--limit N` | Keeps only the first N drugs |

The build drops PTs where `labeltext.is_nonclinical` is true before any query. A rerun sends only the requests that are not cached yet, so an interrupted build resumes where it stopped.

`drugs_v1.txt` and `pairs_v1.txt` are generated. To change them, edit the sources and rerun `python -m pipeline.omics.lists`. The drug list is the union, in this order, of the 31 drugs of the SIDER pilot reference set (`korea-agentic-hackathon-2026/eval/refsets/pilot_sider_2026-09-28.json.gz`, override with `--sider`), the 11 SignalLab presets (`web/src/pages/SignalLab.tsx`), the 3 CLI watchlist drugs (`agent/flygate.py` `DEFAULT_WATCHLIST`), the 9 Time Machine drugs (`web/public/data/faers/backtest.json`), and the 224 primary-suspect drugs of the demo cases (`api/_data/cases.json.gz`). That gives 245 drugs. The pair list holds the 10 watchlist pairs and the 9 Time Machine pairs. `tests/test_lists.py` fails when a list drifts from its sources.

## Cache

Every request is a canonical JSON key: `{"tool", "arguments"}` for a ToolUniverse tool, `{"graphql", "query", "variables"}` for Open Targets GraphQL, and `{"get"}` for the OLS ontology record. The sha1 of the key names the file.

```
$OMICS_DIR/<source>/<sha1>.json    {"request": <key>, "retrieved": "YYYY-MM-DD", "response": <payload>}
```

`<source>` is `opentargets`, `gtex`, `dgidb`, `ols`, `hpo`, or `mondo`. The cache holds successful responses only. A failed request is retried 3 times, then becomes `null` in the extract and one entry in `errors[]`. The build never writes 0 in place of a missing value. One upstream error is an answer and gets cached: Open Targets "returned no disease for ID" means the term is not in its disease index. The build then walks the HPO parents for HP terms, as section 3 of the design describes.

`tests/cache/` is a hand-written replay cache in the same layout. `python -m pipeline.omics.tests.make_replay_cache` rewrites it. `test_cache_replay_reproduces_fixture_bytes` runs the build on it with the network replaced by a test failure and compares the output with `tests/fixtures/omics_fixture.json.gz` byte for byte.

## Versions

The `versions` block of the extract records these values.

| Key | Where it comes from |
|---|---|
| `tooluniverse` | `1.5.7`, the pinned build dependency |
| `opentargets` | GraphQL `meta.dataVersion`, as `year.month` with `.iteration` when present (the pilot's format) |
| `gtex` | `gtex_v10`, the dataset every GTEx query names |
| `ols_efo`, `hpo`, `mondo` | `config.version` of the OLS ontology records `efo`, `hp`, `mondo`. HPO and Mondo searches go to JAX and Monarch, which may serve a different release |

`asof` is the latest retrieval date among the cached responses the build read.

## Coverage table

The build prints this table at the end. It counts drugs planned, in the extract, and with targets. It counts targets, how many have a `safetyLiabilities` field, and how many have GTEx values. It counts distinct PTs planned, nonclinical PTs dropped, and PTs mapped by label, synonym, or not at all. It reports the mapping rate, the organ-candidate rate among mapped terms, the pairs planned and written, and the pairs with an L4 record. Per source and host it counts calls read from cache, sent, not cached (dry run), and failed. It ends with the number of `errors[]` entries and the versions block.

## Recorded numbers

### Dry run on the v1 lists, empty cache (2026-10-26)

This is the command above with `--dry-run` and an empty `OMICS_DIR`. The lists plan 245 drugs, 1,737 distinct PTs after dropping 173 nonclinical ones, and 16,248 pairs.

| Source | Host | Calls not cached |
|---|---|---|
| ols | www.ebi.ac.uk | 1,740 |
| hpo | ontology.jax.org | 1,737 |
| mondo | api.monarchinitiative.org | 1,737 |
| opentargets | api.platform.opentargets.org | 246 |
| gtex | gtexportal.org | 1 |
| total | | 5,461 |

A dry run can count only calls whose inputs are known. The 1,737 searches per ontology are an upper bound, because mapping stops at the first exact match. The ols row adds 3 ontology version reads. The opentargets row is 245 drug-name lookups plus the `meta` query. Calls that depend on responses not cached yet are not in the table. Each resolved drug adds 1 mechanism query and 1 DGIdb query. Each target adds 2 Open Targets queries (safety and the association dump) and 1 GTEx query. Each mapped PT adds 1 ancestor query, and each new HP ancestor adds 1 `HPO_get_term` call. Terms outside the Open Targets index also need one HPO parents call per step up the hierarchy.

### Limited run, NIRAPARIB and CLOZAPINE (2026-10-26)

This run used `--drugs` with the two names, `--pairs pipeline/omics/pairs_v1.txt`, and `--limit 2`, with the network on. It took 4 minutes on a compute node, starting from 64 cached responses of an earlier 3-PT probe.

| | |
|---|---|
| drugs | 2 in extract, both resolved by exact name (NIRAPARIB `CHEMBL1094636`, CLOZAPINE `CHEMBL42`) |
| targets | 4 (PARP1, PARP2, HTR2A, DRD2). 2 have a `safetyLiabilities` field, HTR2A with 42 liabilities and DRD2 with 37 after merging. All 4 have 54 GTEx values |
| PTs | 114 planned (21 nonclinical dropped), 61 label, 18 synonym, 35 none |
| mapping | 79/114 (69.3%) |
| organs | 32/79 (40.5%) of mapped terms |
| pairs | 135, with an L4 record 92, `safety_match` not empty 8 |
| calls sent | hpo 216, ols 105, opentargets 71, mondo 35, failed 0 |
| errors | 2, both `no_ancestors` (`MONDO_0004842`, `EFO_0009631`) |
| versions | opentargets `26.09`, ols_efo `3.95.0`, hpo `2026-09-01`, mondo `2026-10-06` |

A second run from the cache sent nothing and wrote a byte-identical file.

### Full build

Ticket 07 records the drug count, target count, PT count, mapping rate, organ-candidate rate, call count, and failure count of the full build here.

## Recorded numbers (v1 build, 2026-10-26)

Full build on a cpu-core node, job 8352682, then one rerun from the cache to retry 8 failed calls (7 Mondo, 1 HPO; the HPO one, an HTTP 400, stayed failed). Output `api/_data/omics.json.gz`, 389,610 bytes.

| Measure | Value |
|---|---|
| drugs planned / in extract / with targets | 245 / 245 / 184 (27 had no exact Open Targets name match) |
| targets | 315, safety field present for 117, GTEx recorded for 315 |
| PTs planned | 1,737 (173 nonclinical dropped) |
| mapping | 788 / 1,737 = 45.4% (label 685, synonym 103, none 949). Pilot: 24.5% |
| organ candidates | 294 / 788 mapped terms = 37.3% |
| pairs | 16,248, with an association row 8,745 |
| calls sent (first run) | 6,739 (opentargets 1,795, hpo 1,941, ols 1,623, mondo 929, gtex 311, dgidb 140), 8 failed |
| errors in extract | 33 (32 `no_ancestors`, 1 HPO HTTP 400) |
| versions | opentargets 26.09, gtex_v10, ols_efo 3.95.0, hpo 2026-09-01, mondo 2026-10-06, tooluniverse 1.5.7 |

Demo pairs were chosen with `python -m pipeline.omics.pick_demo_pairs`, which reads the extract and lists pairs whose `safety_match` has a `term` relation and whose no-literature association score is above 0. Honest negative: NIRAPARIB|thrombocytopenia (PARP1 and PARP2 `safety: null`, association 0.0125 with no-literature 0.0, mapped by label to HP_0001873). Positive: PIMAVANSERIN|hallucination (HTR2A liability "hallucinations" HP_0000738, sources Bowes et al. 2012 and Lynch et al. 2017, PMIDs 23197038 and 28216264; association 0.486, no-literature 0.484). PIMAVANSERIN is one of the demo-case drugs.

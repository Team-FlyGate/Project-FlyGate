# 07: Real build, committed extract, and demo pair selection

**What to build:** The production extract exists in `api/_data/`, built from the v1 drug and pair lists on a compute node, with its coverage numbers recorded in the pipeline README and the design doc. Running the CLI and the API on the real extract shows niraparib-thrombocytopenia as the honest negative (no recorded liabilities for PARP1 and PARP2, no-literature association 0) and one positive pair, chosen from the data, where a liability matches the term or its ancestor. Both pairs are named in the PR description for the slides.

**Blocked by:** 02, 03

**Status:** ready-for-agent

- [ ] `drugs_v1.txt` and `pairs_v1.txt` committed, built as the documented union (SIDER 31, presets 11, watchlist 3, Time Machine 9, 224 case drugs; top-80 PTs, case top-3 reactions, watchlist and Time Machine pairs)
- [ ] `--dry-run` call count recorded before the run; the run finishes inside the SLURM allocation
- [ ] `api/_data/omics.json.gz` committed; size and record counts noted; Vercel include pattern already covers it
- [ ] Coverage table (drugs, targets, PTs, mapping rate, organ-candidate rate, calls, failures, versions) written to the pipeline README and summarized in the design doc
- [ ] Honest-negative pair verified on the real extract through the CLI and the API
- [ ] Positive demo pair selected by a documented query over the extract (not by memory) and verified the same way
- [ ] Full suite green with the real extract in place

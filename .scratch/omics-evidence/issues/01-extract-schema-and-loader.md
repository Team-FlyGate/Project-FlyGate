# 01: Extract schema, fixture, and omics loader with item composition

**What to build:** A reviewer-facing Python module can answer "what omics evidence exists for drug X and reaction Y" from a compressed extract file. Given the fixture extract, `pair("NIRAPARIB", "thrombocytopenia")` returns the pair record, `items(pair)` returns L1 to L4 evidence items with IDs, `what` text, and numbers, and `items_for_memo(pair)` returns the capped subset. A missing file yields an empty structure, and an unknown drug or pair yields `None`. This ticket also fixes the extract schema that tickets 02 and 03 build against, and ships a small fixture extract (two drugs, one honest-negative pair, one pair with a matched liability, one unmapped term) under the tests tree.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Fixture extract exists, is gzipped JSON with `asof`, `versions`, `drugs`, `targets`, `terms`, `pairs`, `errors`, and loads through the cached loader
- [x] Loader returns the empty structure when the file is missing and tests can swap the data path and clear the cache
- [x] `pair`, `drug_pairs`, `drugs` normalize input with upper and lower case only and keep `\` in combination-product keys
- [x] `items` yields one L1 per target, one L2 per liability with `match` in `term`, `ancestor`, `none`, L3 per candidate tissue (top 5 by TPM when no candidates), one L4; IDs use the four `omics:` prefixes
- [x] `items_for_memo` caps to 5 L1, matched L2 only, 5 L3 inside candidates, 1 L4
- [x] Unmapped term yields no L4, L2 all `none`, L3 top 5
- [x] `safety: null` and absent association are reported as "nothing recorded", never as 0
- [x] Every `what` ends with the fixed population-level sentence and is identical for the same ID across pairs
- [x] Tests pass offline with the full suite green

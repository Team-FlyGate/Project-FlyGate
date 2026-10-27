# 05: Dashboard page `/#/omics` and grade-card count

**What to build:** A dashboard visitor opens `/#/omics`, picks a drug from the extract's drug list, sees its pairs, selects one, and reads a per-layer table: targets, liabilities with match highlighting and PMIDs, tissue expression with TPM and rank, association scores with the literature-only flag, plus the mapping status and organ-candidate provenance. On the Signal Lab grade card, the visitor sees "omics evidence: n items" linking to the page. Pairs outside the extract show "not in the extract". Both Korean and English views are complete.

**Blocked by:** 03

**Status:** done

- [x] Page registered in the FlyVigilance group and reachable at `/#/omics`, with `?drug=&pt=` deep links
- [x] Drug picker fed by `/api/omics/drugs`; pair list by `/api/omics?drug=`; table by `/api/omics?drug=&pt=`
- [x] Matched liabilities (`term`, `ancestor`) visually distinct from `none`; "nothing recorded" shown for `null` safety
- [x] Mapping status and organ provenance (ancestor, word) visible
- [x] 404 renders "not in the extract" in both languages
- [x] Grade card shows the omics count from `/api/grade` and links to the page
- [x] `npm run build` in `web/` succeeds with no type errors
- [ ] Manual check in the dev server on the two demo pairs recorded in the PR description

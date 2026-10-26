# 04: Omics items in the evidence bundle and critic rule R14

**What to build:** When the System-2 assessor builds its evidence bundle for a case, each principal reaction's capped omics items appear in the catalog with their IDs, so the Nemotron memo can cite `omics:` IDs and the critic's tier-1 ID check and tier-2 number check accept them. The critic's rule list gains R14 (mechanistic plausibility is population-level and never case causality; absence is not evidence against), and every place that enumerates the rules or counts them says 14. The grade's `gaps` gains one line saying omics evidence is not reflected in the grade, with an English translation on the card.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Bundle catalog includes `items_for_memo` for each reaction the bundle already selects; `ids` includes them; module docstring lists the four prefixes
- [ ] A memo claim citing an `omics:` ID passes tier 1; a claim citing a non-existent `omics:` ID fails tier 1
- [ ] R14 present in the rule list and in the system prompt; the skills page rule list, the glossary "13 rules" strings, and the critic skill doc say 14 and include R14
- [ ] `gaps` gains the Korean line and `GAP_EN` the English counterpart
- [ ] Bundle test on the ticket-01 fixture with network functions patched, offline
- [ ] Full suite green

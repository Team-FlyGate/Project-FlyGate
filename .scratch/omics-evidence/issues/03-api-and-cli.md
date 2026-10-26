# 03: API routes and `flygate omics` command

**What to build:** An agent operator runs `flygate omics NIRAPARIB "Thrombocytopenia"` and gets the items and `evidence_ids` as JSON; for a drug outside the extract the command prints `found: false` with a reason and exits 0. A dashboard or script calls `GET /api/omics?drug=NIRAPARIB&pt=thrombocytopenia`, `GET /api/omics?drug=NIRAPARIB`, and `GET /api/omics/drugs` and gets the same data, with 404 for unknown pairs. `/api/grade` gains an `omics` block with the item count and mapping status without any change to the grade module. The chat agent accepts `/omics`.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Three routes with query parameters (not path variables), rate-limit key `omics`, 404 on unknown drug or pair, endpoint list in the module docstring updated
- [ ] `/api/grade` response includes `omics: {count, mapping}` sourced from the extract; grade, class, and flags unchanged
- [ ] `flygate omics` registered with help text, output includes `cmd`, `drug`, `pt`, `found`, `items`, `evidence_ids`
- [ ] Unknown drug or pair gives `found: false`, a reason string, empty `evidence_ids`, exit code 0
- [ ] `ALLOWED` contains `omics`; `HELP` and the chat `SYSTEM` command list mention it; banner says 8 tools; `TOOLS.md` has an entry
- [ ] Existing subcommand-set test and banner-count test updated to the new values
- [ ] API tests through `TestClient` and CLI tests through the entry point, both on the ticket-01 fixture, offline
- [ ] Full suite green

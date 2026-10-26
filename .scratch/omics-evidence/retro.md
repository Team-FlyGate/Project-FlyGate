# Retro notes: omics-evidence session (running log)

Candidates for environment improvements, collected while the work runs. Presented at the end, ordered by severity. Each entry: category, what happened, proposed change.

## Collected so far (design phase, 2026-10-26)

- Tool economy. The ToolUniverse MCP server failed to connect because the uv cache resolved `uvx tooluniverse` to the stale PyPI package 0.1.4. Fix was a one-time refresh. Proposed: pin `tooluniverse==1.5.7` in the plugin's MCP command or document the refresh in the repo README under "agent setup".
- Navigation. Finding the pilot code took a search of the old repo and a branch name. Proposed: a one-line pointer in `docs/EVALUATION.md` section 7 to `korea-agentic-hackathon-2026@omics-plausibility:scripts/omics_plausibility.py`.
- Automated checks. The repo has no lint or typecheck guardrail wired for Python (`pytest` only, run by hand). Proposed: a `make check` or a `scripts/check.sh` that runs `pytest -q tests` and `cd web && npm run build`, and a pre-commit hook calling it.
- Coding standards. The design review found hard-coded counts in three places (`'7 tools'` in the banner and its test, "13 rules" in the glossary and skills page). Mechanical: a test that derives the tool count from `chat.ALLOWED` and the rule count from `OVERCLAIM_RULES` would remove the drift. Proposed as part of ticket 03 and 04.
- Information access. `gh` is not installed on the HPC, so GitHub Issues cannot be written from the agent session. Local markdown tracker chosen. Proposed: install `gh` in association space or keep local markdown as the documented default.
- Tool economy. `humanize-korean` chunked a 15,510-character doc into 12 pieces, several under 500 characters. Single call was fine. Proposed: nothing in this repo; note for the plugin.

## Collected during ticket 01 (2026-10-26)

- Automated checks / information access. The repo `.venv` on this machine is Python 3.9 without pytest, while `api/` uses `dict | None` syntax (3.10+). The README's `.venv/bin/python -m pytest` instruction fails silently for a new agent. Proposed: a `scripts/check.sh` that asserts Python >= 3.10 and prints the venv to use; or a `requirements-dev.txt` plus a one-line setup note naming the miniforge `python3.10`.
- Tool economy. `rsc` has no `cpu-test` partition, so the institute rule "use cpu-test for smoke tests" cost one failed srun. Proposed: note in the project CLAUDE.md that `rsc` uses `cpu-core` with short `-t` for smoke tests.
- Coding standards (mechanical). Ticket 01 left `rank_of_54` as a key name while the count is dynamic. Harmless now, misleading later. Proposed: reviewer rule "key names must not encode a constant that the value can contradict".
- Navigation. Delegates needed the fixture-generation script, which lives outside the repo. Proposed: commit `tests/fixtures/make_omics_fixture.py` in ticket 02 or 07 so the fixture is reproducible from the repo.

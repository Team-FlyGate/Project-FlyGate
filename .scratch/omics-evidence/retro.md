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

## Collected during tickets 03 and 04 (2026-10-26)

- Automated checks. `agent/export_agent_json.py` asserts `set(sub.choices) == set(CLI)` but the parser has `login` and `chat` that `CLI` omits, so the script appears to fail at HEAD already (reported by the ticket-03 delegate from reading the code; not run because the venv lacks `yaml`). Proposed: a test that imports the script's table and compares it with `build_parser()` choices, and `pyyaml` in a dev requirements file.
- Coding standards (judgement). The "not in the omics extract" reason is computed in both `index.omics_query` and `flygate.cmd_omics`. Proposed: `omics.missing(drug, pt)` so the message has one owner. Low priority; note for review.
- Navigation. Rule counts and command tables are duplicated in at least 14 files (web pages, glossary, READMEs, ARCHITECTURE, AGENT, two skill docs, agent workspace). The ticket-04 test now derives the count for three of them; the rest were fixed by hand. Proposed: extend `test_rule_count_matches_every_place_that_lists_rules` to grep all of `web/src`, `docs/*.md`, `README*.md`, `skills/*/SKILL.md`, `agent/workspace/*.md` (excluding `docs/readme-versions`) for `R1[–-]R\d+` and `\d+(가지 |)규칙|\d+ rules` and compare with `len(OVERCLAIM_RULES)`.
- Tool economy. Three delegates in one working tree saw each other's half-written tests once (14 transient failures). No harm, but a worktree per delegate would have avoided the noise. The Agent tool's worktree isolation was not used because its worktree location is not configurable to the association tmp path. Proposed: an `EnterWorktree`-based recipe that puts worktrees under `/data/hps/assoc/private/rsc/user/ybae/tmp/worktrees/`.

## Collected after the session restart (2026-10-26)

- Information access. The Claude Code process restarted while tickets 02 and 05 were running. Their files survived on disk but their reports did not, so two fresh delegates had to re-assess state from scratch. Proposed: every code delegate writes `.scratch/<feature>/progress-<ticket>.md` (criteria done, commands run, open questions) after each red-green cycle, so a restart loses minutes, not the brief.

## Collected during ticket 02 (2026-10-26)

- Coding standards (judgement). The first organ rule matched any shared word, so "blood" selected both Blood and Blood Vessel in all 16 blood terms of the limited run. Tightened to "every word of the tissue-group name". Lesson for the design doc: state set relations exactly (subset, not intersection) when a rule is meant to be deterministic.
- Information access. `uv run` picked the system Python 3.9 until `--python 3.12` was added; ToolUniverse refuses < 3.10. Proposed: put the interpreter flag in every documented command and in `pipeline/omics/README.md` (done).
- Tool economy. Open Targets answers "returned no disease for ID" for terms outside its index; treating that as a failure meant it was never cached and re-sent every run. Proposed as a reviewer rule: a deterministic "not found" from an upstream is an answer to cache, not an error to retry.
- Navigation. OLS EFO and Mondo search responses carry no synonyms through ToolUniverse; all synonym matches came from HPO. `rows: 5` misses some exact terms (eosinophilia). Candidates for a v1.1 mapping improvement, recorded in the pipeline README.

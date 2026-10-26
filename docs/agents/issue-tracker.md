# Issue tracker

Issues live as local markdown files in this repo. The `gh` CLI is not available on the HPC where the agent runs, so GitHub Issues are not written from the agent session.

- Location: `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, one file per ticket, numbered from `01` in dependency order.
- Spec: `.scratch/<feature-slug>/spec.md`.
- Triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. The label is the `Status:` line in each ticket file.
- Blocking edges: the `Blocked by:` line in each ticket names the ticket numbers that must finish first.
- Done: change `Status:` to `done` and tick the acceptance criteria. Do not delete ticket files.
- Migration: after 2026-10-29 the team may move open tickets to GitHub Issues on `Team-FlyGate/Project-FlyGate`. Paste the file body as the issue body.

Current feature: `omics-evidence` (branch `feat/omics-evidence`).

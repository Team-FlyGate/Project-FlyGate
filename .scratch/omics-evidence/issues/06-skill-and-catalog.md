# 06: `pv-omics-evidence` skill and catalog updates

**What to build:** A hackathon judge browsing the skills screen or the skills README sees a twelfth FlyVigilance skill, `pv-omics-evidence`, describing the four layers, the evidence-ID prefixes, the R14 limit, and the CLI and API contract, with the same frontmatter fields as the other eleven. The skills JSON that feeds the dashboard includes it, and the README counts are correct.

**Blocked by:** 04

**Status:** done

- [x] `SKILL.md` with all required frontmatter fields (`name`, `title`, `version`, `description`, `license`, `compatibility`, `metadata.author/domain/tags/layer/model`) and an execution contract that points at real functions and routes
- [x] skill-card generated with the NVIDIA generator when the scripts are available; otherwise the PR notes it as pending
- [x] `evals/evals.json` with at least three tasks whose ground truth comes from the ticket-01 fixture
- [x] Skills README tables and counts (11 to 12 FlyVigilance skills, 16 to 17 total) updated
- [x] `pipeline/build_skills.py` rerun; `web/public/data/skills.json` includes the new skill
- [x] Full suite green


## Appendix E: `.github/copilot-instructions.md` (create in Phase 1)

````markdown
# Shell Data Platform CI/CD: agent instructions

The authoritative context is `HANDOFF.md` in the workspace root. Read it before any task. Section 5 is the target
design; do not redesign it. Work phase by phase (HANDOFF §4) and stop for review after each phase or step.

Rules (HANDOFF §2, summary):
- Read-only by default; ask before creating, changing or deleting anything in Azure, Databricks, GitHub settings or databases.
- Never touch QA, UAT or PROD directly. Never grant access; record gaps in environment/ACCESS_GAPS.md.
- No secrets anywhere. All code through branches and PRs; never push to main.
- Every fact goes in environment/ENVIRONMENT_FACTS.md with its source; unknown → UNKNOWN, ask.
- Do not move or delete existing files in this folder.
- After each step: update STATUS.md (done / in progress / blocked / next) and DECISIONS.md (append-only).

Living files: STATUS.md, DECISIONS.md, environment/{INVENTORY,ENVIRONMENT_FACTS,CURRENT_PROCESS,REQUIREMENTS,ACCESS_GAPS}.md.
New platform repo: shell-data-platform/ (Phase 4).
````

## Appendix F: Task prompts (create in Phase 1 under `.github/prompts/`)

Each file starts with front matter. In Copilot Chat (Agent mode), run them by typing `/` and the name.

`.github/prompts/phase1-setup.prompt.md`
````markdown
---
name: phase1-setup
agent: agent
description: 'Phase 1 - inventory devops-cicd and set up living files'
---
Do HANDOFF.md §4 Phase 1 exactly. Read-only except creating the new files listed there. Stop and report.
````

`.github/prompts/phase2-discover.prompt.md`
````markdown
---
name: phase2-discover
agent: agent
description: 'Phase 2 - discover the existing environment (read-only)'
---
Do HANDOFF.md §4 Phase 2. Use the existing files first, then the read-only commands in the table.
Every value needs a source. Answer the §6 open questions at the top of ENVIRONMENT_FACTS.md. Write CURRENT_PROCESS.md.
Stop and report the answers, top 5 risks, and anything you could not access.
````

`.github/prompts/phase3-requirements.prompt.md`
````markdown
---
name: phase3-requirements
agent: agent
description: 'Phase 3 - requirements, gap analysis, access gaps, admin email'
---
Do HANDOFF.md §4 Phase 3: REQUIREMENTS.md from §5 vs Phase 2 facts; ACCESS_GAPS.md checking every §5.12 item
(Exists / Missing / Cannot check, with evidence) plus a one-page admin email of only the Missing items, DEV first;
decisions needed, recorded as "Proposed" in DECISIONS.md. Do not grant anything. Stop for review.
````

`.github/prompts/phase4-step.prompt.md`
````markdown
---
name: phase4-step
agent: agent
description: 'Phase 4 - implement one development step'
argument-hint: 'step number, e.g. 4.1'
---
Implement HANDOFF.md §4 Phase 4 step ${input:step} only, following §5 and using real names from ENVIRONMENT_FACTS.md.
Work on a branch in shell-data-platform/, run the acceptance checks for that step, open a PR, update STATUS.md, then stop.
Ask before any command that changes Azure, Databricks, a database or GitHub settings.
````

`.github/prompts/status.prompt.md`
````markdown
---
name: status
agent: agent
description: 'Refresh STATUS.md and give a 10-line update'
---
Refresh STATUS.md from the workspace, open PRs and recent workflow runs (gh pr list, gh run list), ACCESS_GAPS.md and
DECISIONS.md. Reply in 10 lines: done, in progress, blocked (by whom), next step, open questions still UNKNOWN.
````

# Archify (diagram skill for coding agents)

`archify-3.2.0.zip` is the Archify agent skill (v3.2.0, from https://github.com/tt-a1i/archify,
commit 51a291770851ad27a400cca73c753c166b5e0c65), dual-licensed Apache-2.0 / MIT. Licence and notice files are inside the zip.
It turns a JSON description into a checked, standalone HTML diagram (workflow, architecture, sequence, lifecycle, ERD, …).
It needs Node.js 18+ and, for its browser check, Chrome/Chromium/Edge (or `ARCHIFY_CHROME` pointing to one).

## Install for your local agent (no repo clone needed)

Unzip into one of the skill folders your agent reads:

| Agent | Workspace (per project) | User (all projects) |
|---|---|---|
| VS Code GitHub Copilot | `<workspace>/.github/skills/` or `.claude/skills/` | `~/.copilot/skills/` or `~/.claude/skills/` |
| Claude Code | `<workspace>/.claude/skills/` | `~/.claude/skills/` |

```bash
# example: PDX_Projects/devops-cicd as the workspace
unzip archify-3.2.0.zip -d PDX_Projects/devops-cicd/.github/skills/
node PDX_Projects/devops-cicd/.github/skills/archify/bin/archify.mjs doctor
```
Alternative with internet access: `npx skills add tt-a1i/archify`.

## Diagrams in this repo

`docs/diagrams/archify/*.archify.json` are the sources; regenerate with
`node <skills>/archify/bin/archify.mjs finalize workflow docs/diagrams/archify/<name>.archify.json docs/diagrams/archify/<name>.html --quality showcase --json`.

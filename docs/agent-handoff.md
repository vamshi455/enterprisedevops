# Handing this work to the local agent (VS Code + GitHub Copilot)

1. In `PDX_Projects/devops-cicd/` (keep everything already there), copy in from this repo:
   - `.github/copilot-instructions.md` → `PDX_Projects/devops-cicd/.github/copilot-instructions.md`
   - `.github/prompts/` → `PDX_Projects/devops-cicd/.github/prompts/`
   - `AGENTS.md` → `PDX_Projects/devops-cicd/AGENTS.md`

   If `devops-cicd/.github/copilot-instructions.md` already exists, append ours under a heading instead of replacing it.
2. Open `PDX_Projects/devops-cicd` as the VS Code workspace folder. The instructions load automatically.
3. In Copilot Chat choose **Agent** mode and your Claude model, then type `/00-bootstrap`.
4. Run the prompts in order, reviewing between each: `/01-access-gaps`, `/02-repo-scaffold`, `/03-pr-validation`,
   `/04-feature-env`, `/05-deploy-dev`, `/06-release`, `/07-pilot-story`. Use `/status` any time.

The agent works read-only until you approve a change, never touches QA/UAT/PROD directly, and never grants access itself.

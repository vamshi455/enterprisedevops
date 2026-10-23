#!/usr/bin/env bash
# One-time setup of the GATE 1 policies on main (Azure Repos). Requires: az cli + azure-devops extension.
# Usage: ORG=https://dev.azure.com/shell PROJECT=DataPlatform REPO=shell-data TECHLEADS_GROUP_ID=<guid> ./branch_policies.sh
set -euo pipefail
: "${ORG:?}" "${PROJECT:?}" "${REPO:?}" "${TECHLEADS_GROUP_ID:?}"
az devops configure --defaults organization="$ORG" project="$PROJECT"
REPO_ID=$(az repos show --repository "$REPO" --query id -o tsv)
common=(--repository-id "$REPO_ID" --branch main --blocking true --enabled true)

# 1. Every PR must be linked to a story/bug  (the "must" from the Marathon process)
az repos policy work-item-linking create "${common[@]}"
# 2. Tech lead review: >=1 reviewer, author can't approve own PR, reset votes on new pushes
az repos policy approver-count create "${common[@]}" --minimum-approver-count 1 \
   --creator-vote-counts false --allow-downvotes false --reset-on-source-push true
az repos policy required-reviewer create "${common[@]}" --required-reviewer-ids "$TECHLEADS_GROUP_ID" \
   --message "Tech lead review: standards, naming, parameterisation"
# 3. All comments resolved
az repos policy comment-required create "${common[@]}"
# 4. Squash merge ONLY -> one PR == one commit on main == one unit of cherry-pick
az repos policy merge-strategy create "${common[@]}" --allow-squash true \
   --allow-no-fast-forward false --allow-rebase false --allow-rebase-merge false
# 5. Build validation (pipelines/pr-validation.yml must be registered as pipeline 'shell-data-pr-validation')
PIPE_ID=$(az pipelines show --name shell-data-pr-validation --query id -o tsv)
az repos policy build create "${common[@]}" --build-definition-id "$PIPE_ID" \
   --display-name "PR validation" --manual-queue-only false --queue-on-source-update-only true --valid-duration 720
echo "main is now gated."

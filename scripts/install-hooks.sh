#!/usr/bin/env bash
# =============================================================================
# Install Tattvashila git hooks
#
# Usage:  bash scripts/install-hooks.sh
#
# Points git's hooksPath to .githooks/ so the pre-commit secret scanner
# runs automatically on every commit in this repository.
# Does NOT affect any other repository on your system.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
HOOKS_DIR="${REPO_ROOT}/.githooks"
GIT_HOOKS_DIR="${REPO_ROOT}/.git/hooks"

if [[ ! -d "$HOOKS_DIR" ]]; then
    echo "ERROR: .githooks/ directory not found at ${HOOKS_DIR}"
    echo "       Are you running this from the repo root?"
    exit 1
fi

# Make all hooks executable
chmod +x "${HOOKS_DIR}"/pre-commit

# Strategy 1 — preferred: use git config hooksPath (works in standard git envs)
if git config --local core.hooksPath .githooks 2>/dev/null; then
    echo ""
    echo "✓  Git hooks installed via git config core.hooksPath"
    echo "   Hook directory: .githooks/"
    echo "   Active hooks:   pre-commit (secret & hygiene scanner)"

# Strategy 2 — fallback: copy directly to .git/hooks/ (works when git config is restricted)
elif cp "${HOOKS_DIR}/pre-commit" "${GIT_HOOKS_DIR}/pre-commit" 2>/dev/null && \
     chmod +x "${GIT_HOOKS_DIR}/pre-commit"; then
    echo ""
    echo "✓  Git hooks installed by copying to .git/hooks/"
    echo "   Active hooks:   pre-commit (secret & hygiene scanner)"
    echo "   NOTE: The hook was copied, not symlinked. Re-run this script"
    echo "         if you update .githooks/pre-commit."

else
    echo ""
    echo "⚠  Could not install hooks automatically (restricted environment)."
    echo ""
    echo "   Run these commands manually in your terminal:"
    echo "     git config --local core.hooksPath .githooks"
    echo "   OR:"
    echo "     cp .githooks/pre-commit .git/hooks/pre-commit"
    echo "     chmod +x .git/hooks/pre-commit"
    echo ""
    echo "   The hook file is ready at: .githooks/pre-commit"
    exit 0
fi

echo ""
echo "   The pre-commit hook runs on every 'git commit' in this repo."
echo "   To bypass in an emergency: SKIP_SECRET_SCAN=1 git commit ..."
echo ""

#!/usr/bin/env bash
set -euo pipefail

# Helper to initialize git and push this repository to GitHub.
# Usage:
#   ./push_to_github.sh --repo-name my-repo --private|--public --remote-url git@github.com:me/my-repo.git
# Or, if you have the GitHub CLI installed, omit --remote-url and pass --repo-name to create it automatically.

show_help(){
  sed -n '1,200p' <<'EOF'
Usage: push_to_github.sh [--repo-name NAME] [--remote-url URL] [--public|--private] [--branch BRANCH]

Examples:
  ./push_to_github.sh --repo-name jobpilot --public
  ./push_to_github.sh --repo-name jobpilot --remote-url git@github.com:me/jobpilot.git

This script will:
 - ensure git is initialized
 - add a sensible .gitignore (if missing)
 - create the GitHub repo via `gh` if available
 - add remote and push the current branch
EOF
}

REPO_NAME=""
REMOTE_URL=""
VISIBILITY="private"
BRANCH="main"

while [[ $# -gt 0 ]]; do
  case $1 in
    --repo-name) REPO_NAME="$2"; shift 2;;
    --remote-url) REMOTE_URL="$2"; shift 2;;
    --public) VISIBILITY="public"; shift;;
    --private) VISIBILITY="private"; shift;;
    --branch) BRANCH="$2"; shift 2;;
    --help|-h) show_help; exit 0;;
    *) echo "Unknown arg: $1"; show_help; exit 1;;
  esac
done

if [ -z "$REPO_NAME" ] && [ -z "$REMOTE_URL" ]; then
  echo "Either --repo-name or --remote-url is required." >&2
  show_help
  exit 1
fi

ROOT_DIR=$(pwd)

if [ ! -d .git ]; then
  git init
  git checkout -b "$BRANCH"
fi

# Add main .gitignore if repo root .gitignore is missing
if [ ! -f .gitignore ]; then
  cat > .gitignore <<'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*.pyo
venv/
env/

# Node
node_modules/
/.next/

# Env
.env
.env.*

# Other
.DS_Store
GITIGNORE
  git add .gitignore
fi

git add -A
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "chore: initial commit"
fi

if [ -n "$REMOTE_URL" ]; then
  git remote remove origin 2>/dev/null || true
  git remote add origin "$REMOTE_URL"
  git push -u origin "$BRANCH"
  echo "Pushed to remote $REMOTE_URL"
  exit 0
fi

# If we reach here, we have REPO_NAME and no REMOTE_URL. Try using gh to create.
if command -v gh >/dev/null 2>&1; then
  echo "Creating GitHub repo using gh: ${REPO_NAME} (${VISIBILITY})"
  gh repo create "$REPO_NAME" --${VISIBILITY} --source=. --remote=origin --push
  echo "Repository created and pushed via gh."
  exit 0
else
  echo "GitHub CLI 'gh' not found. Please either install 'gh' or provide --remote-url (e.g. git@github.com:me/${REPO_NAME}.git)." >&2
  exit 1
fi

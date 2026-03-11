#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source .venv/bin/activate

rm -rf dist/

pytest
ruff check src/
mypy src/

PUBLISHED=$(curl -sf https://pypi.org/pypi/octivas/json | python -c "import sys,json; print(json.load(sys.stdin)['info']['version'])")
IFS='.' read -r MAJOR MINOR PATCH <<< "$PUBLISHED"
NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"

sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
sed -i "s|octivas-python/.*\"|octivas-python/$NEW_VERSION\"|" src/octivas/client.py

echo "Published version: $PUBLISHED → Building $NEW_VERSION"

python -m build
# run these manually:
#twine upload dist/*

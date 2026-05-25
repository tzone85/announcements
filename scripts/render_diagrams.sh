#!/usr/bin/env bash
# Regenerate all architecture SVGs from PlantUML sources.
# Run from any directory. Requires plantuml on PATH (brew install plantuml).
set -euo pipefail
cd "$(dirname "$0")/../docs/architecture"
plantuml -tsvg -nometadata *.puml
echo "rendered: $(ls *.svg | wc -l | tr -d ' ') svg files"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$ROOT_DIR/build"
MD_FILE="$ROOT_DIR/requirements_specification.md"
TEX_FILE="$BUILD_DIR/requirements_specification.tex"
PDF_FILE="$BUILD_DIR/requirements_specification.pdf"

mkdir -p "$BUILD_DIR/plantuml-diagrams"

if [[ ! -f "$ROOT_DIR/tools/plantuml.jar" ]]; then
  echo "Missing $ROOT_DIR/tools/plantuml.jar" >&2
  echo "Download it from https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" >&2
  exit 1
fi

export PLANTUML_JAR="$ROOT_DIR/tools/plantuml.jar"
export GRAPHVIZ_DOT="${GRAPHVIZ_DOT:-/usr/bin/dot}"

pandoc "$MD_FILE" \
  --from markdown+pipe_tables+fenced_code_blocks+fenced_code_attributes \
  --to latex \
  --standalone \
  --lua-filter "$ROOT_DIR/plantuml-filter.lua" \
  --template "$ROOT_DIR/requirements_template.tex" \
  --resource-path "$ROOT_DIR:$ROOT_DIR/../assets" \
  --output "$TEX_FILE"

(
  cd "$BUILD_DIR"
  lualatex -shell-escape -interaction=nonstopmode "$(basename "$TEX_FILE")"
  lualatex -shell-escape -interaction=nonstopmode "$(basename "$TEX_FILE")"
)

cp "$PDF_FILE" "$ROOT_DIR/requirements_specification.pdf"
echo "Done: $ROOT_DIR/requirements_specification.pdf"

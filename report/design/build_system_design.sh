#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="$(cd "$ROOT_DIR/.." && pwd)"
REQ_DIR="$REPORT_DIR/requirements"
BUILD_DIR="$ROOT_DIR/build"
MD_FILE="$ROOT_DIR/system_design_specification.md"
TEX_FILE="$BUILD_DIR/system_design_specification.tex"
PDF_FILE="$BUILD_DIR/system_design_specification.pdf"

mkdir -p "$BUILD_DIR/plantuml-diagrams"

if [[ ! -f "$REQ_DIR/tools/plantuml.jar" ]]; then
  echo "Missing $REQ_DIR/tools/plantuml.jar" >&2
  echo "Download it from https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" >&2
  exit 1
fi

export PLANTUML_JAR="$REQ_DIR/tools/plantuml.jar"
export GRAPHVIZ_DOT="${GRAPHVIZ_DOT:-/usr/bin/dot}"

pandoc "$MD_FILE" \
  --from markdown+pipe_tables+fenced_code_blocks+fenced_code_attributes \
  --to latex \
  --standalone \
  --listings \
  --lua-filter "$REQ_DIR/plantuml-filter.lua" \
  --template "$ROOT_DIR/system_design_template.tex" \
  --resource-path "$ROOT_DIR:$REPORT_DIR/assets" \
  --output "$TEX_FILE"

(
  cd "$BUILD_DIR"
  lualatex -shell-escape -interaction=nonstopmode "$(basename "$TEX_FILE")"
  lualatex -shell-escape -interaction=nonstopmode "$(basename "$TEX_FILE")"
)

cp "$PDF_FILE" "$ROOT_DIR/system_design_specification.pdf"
cp "$TEX_FILE" "$ROOT_DIR/system_design_specification.tex"
echo "Done: $ROOT_DIR/system_design_specification.pdf"

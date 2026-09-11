#!/usr/bin/env bash
set -e
MAX_N=${1:-4}                    # 缺省 4
python generate_hierarchy_catalog.py "$MAX_N"

# DOT → PDF：统一 2×2 inch 画布、无白边、300 dpi
for dotf in tex/img/*.dot; do
  pdf="${dotf%.dot}.pdf"
  dot -Tpdf -Gmargin=0 -Gsize="2,2!" -Gdpi=300 "$dotf" -o "$pdf"
done

# 编译各层 LaTeX
for lvl in $(seq 0 "$MAX_N"); do
  (cd tex && pdflatex -interaction=batchmode "lvl${lvl}.tex")
done
echo "✓ catalogs ready: tex/lvl*.pdf"

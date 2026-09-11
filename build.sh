#!/usr/bin/env bash
set -e
# 0. 安装检查
command -v dot >/dev/null || { echo "❌ Graphviz(dot) 未安装"; exit 1; }
command -v pdflatex >/dev/null || { echo "❌ LaTeX 未安装"; exit 1; }

# 1. 生成 DOT & LaTeX
python generate_dag_catalog.py "$@"

# 2. DOT → PDF（统一 2×2 inch 画布，无白边）
for f in tex/img/*.dot; do
  dot -Tpdf -Gmargin=0 -Gsize="2,2!" -Gdpi=300 "$f" -o "${f%.dot}.pdf"
done

# 3. 编译 catalog.pdf
cd tex
pdflatex -interaction=batchmode catalog.tex
pdflatex -interaction=batchmode catalog.tex
echo "✓ output: tex/catalog.pdf"

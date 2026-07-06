#!/bin/bash
# 一键编译 + 清理辅助文件
NAME="${1:-plan_closed}"
xelatex -interaction=nonstopmode "$NAME.tex" && \
xelatex -interaction=nonstopmode "$NAME.tex" && \
rm -f "$NAME.aux" "$NAME.toc" "$NAME.out" "$NAME.log" && \
echo "Done: $NAME.pdf"

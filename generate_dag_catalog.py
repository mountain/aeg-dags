#!/usr/bin/env python3
"""
Enumerate all {+,×}-expressions with n internal nodes (leaves=1),
emit DOT for each DAG, and write a LaTeX catalog.

usage: python generate_dag_catalog.py [n]   # default n=3
"""

import sys, itertools, hashlib
from pathlib import Path

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
IMG_DIR = Path("tex/img"); IMG_DIR.mkdir(parents=True, exist_ok=True)


# ---------- Catalan shapes ----------
def shapes(k):
    if k == 0:
        yield 1               # leaf
    else:
        for l in range(k):
            r = k - 1 - l
            for a in shapes(l):
                for b in shapes(r):
                    yield ('', a, b)  # '' = placeholder op


def label(shape, ops_iter):
    if shape == 1:
        return 1
    op = next(ops_iter)
    return (op, label(shape[1], ops_iter), label(shape[2], ops_iter))


# ---------- evaluation & hashing ----------
OPS = {'+': lambda x, y: x + y, '*': lambda x, y: x * y}
COMMUTATIVE = {'+', '*'}  # 你日后想把 -, / 加进来，只需不放这里


def value(t):
    return 1 if t == 1 else OPS[t[0]](value(t[1]), value(t[2]))


def h(t):
    if t == 1:
        return '1'
    op, l, r = t
    hl, hr = h(l), h(r)
    if op in COMMUTATIVE and hl > hr:   # 关键：对子树哈希排序
        hl, hr = hr, hl
    return hashlib.sha1(f'{op},{hl},{hr}'.encode()).hexdigest()


# ---------- DOT ----------
DOT_HDR = 'digraph G {{\nnode [fontname="Helvetica"];\n{}\n}}\n'


def to_dot(tree):
    nodes, edges = [], []
    cache = {}
    def go(t):
        key = h(t)
        if key in cache:
            return cache[key]
        idx = f'n{len(cache)}'; cache[key] = idx
        if t == 1:
            nodes.append(f'{idx} [label="1",shape=box];')
        else:
            nodes.append(f'{idx} [label="{t[0]}"];')
            for child in (t[1], t[2]):
                cid = go(child)
                edges.append(f'{idx} -> {cid};')
        return idx
    go(tree)
    return DOT_HDR.format('\n'.join(nodes + edges))


# ---------- enumeration ----------
trees = []
for s in shapes(N):
    for lbls in itertools.product(['+','*'], repeat=N):
        t = label(s, iter(lbls)); trees.append(t)


vals = {}
seen = set()
for i, t in enumerate(trees):
    root = h(t)
    if root in seen:  # 已收录 → 跳过
        continue
    seen.add(root)
    idx = len(seen) - 1
    dot_file = IMG_DIR / f"expr_{idx:04d}.dot"
    dot_file.write_text(to_dot(t))
    vals.setdefault(value(t), []).append(idx)


# ---------- LaTeX ----------
tex = [
    r'\documentclass[10pt]{article}',
    r'\usepackage{graphicx}',
    r'\usepackage[margin=1cm]{geometry}',
    r'\begin{document}',
    rf'\section*{{Catalog for $n={N}$ (total {len(trees)} expressions and {len(seen)} independent expressions)}}',
]
for v, ids in sorted(vals.items()):
    tex.append(rf'\subsection*{{Value = {v} ({len(ids)} exprs)}}')
    for j in ids:
        tex.append(r'\begin{minipage}[t]{0.24\linewidth}\centering')
        tex.append(rf'\includegraphics[width=\linewidth,height=\linewidth,keepaspectratio]{{img/expr_{j:04d}.pdf}}')
        tex.append(r'\end{minipage}')
    tex.append(r'\par\bigskip')
tex.append(r'\end{document}')

Path('tex/catalog.tex').write_text('\n'.join(tex))
print(f'Generated {len(trees)} DOT files and tex/catalog.tex')

#!/usr/bin/env python3
"""
Build level‑by‑level DAG catalogs for {+,×} expressions.
Level n == exactly n internal nodes (leaves = 1).
If a subtree hash first appeared at a lower level,
later levels compress it to a diamond node labelled "ref ID".

usage: python generate_hierarchy_catalog.py [MAX_N]   # default 4
"""

import sys, itertools, hashlib, json
from pathlib import Path

MAX_N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
IMG_DIR = Path("tex/img"); IMG_DIR.mkdir(parents=True, exist_ok=True)

# ---------- utilities ----------
def shapes(k):
    if k == 0:
        yield 1
    else:
        for l in range(k):
            for left in shapes(l):
                for right in shapes(k - 1 - l):
                    yield ('', left, right)          # '' = placeholder op

def attach_ops(shape, ops_iter):
    if shape == 1:
        return 1
    op = next(ops_iter)
    return (op, attach_ops(shape[1], ops_iter), attach_ops(shape[2], ops_iter))

OPS = {'+': lambda x, y: x + y, '*': lambda x, y: x * y}
COMM = {'+', '*'}

def val(t): return 1 if t == 1 else OPS[t[0]](val(t[1]), val(t[2]))

def thash(t):
    if t == 1:
        return '1'
    op, l, r = t
    hl, hr = thash(l), thash(r)
    if op in COMM and hl > hr:
        hl, hr = hr, hl
    return hashlib.sha1(f'{op}:{hl}:{hr}'.encode()).hexdigest()

# ---------- global registries ----------
subtree_first_seen = {}          # hash → (expr_id, level)
expr_id = 0                      # running global ID

def to_dot(tree, level):
    """Return DOT string; compress refs to earlier levels."""
    nodes, edges, local = [], [], {}

    def visit(t):
        key = thash(t)

        # compress to ref if seen earlier (< level)
        if key != '1' and key in subtree_first_seen and subtree_first_seen[key][1] < level:
            rid = subtree_first_seen[key][0]
            nid = f'ref_{rid}'
            if nid not in local:
                nodes.append(f'{nid} [label="ref {rid}",shape=diamond,style=dashed];')
                local[nid] = nid
            return nid

        # normal expansion
        if key in local:
            return local[key]
        nid = f'n{len(local)}'
        local[key] = nid
        if t == 1:
            nodes.append(f'{nid} [label="1",shape=box];')
        else:
            nodes.append(f'{nid} [label="{t[0]}"];')
            for child in (t[1], t[2]):
                cid = visit(child)
                edges.append(f'{nid} -> {cid};')
        return nid

    visit(tree)
    content = '\n'.join(nodes + edges)
    return f'digraph G {{\nnode [fontname="Helvetica"];\n{content}\n}}\n'

# ---------- main loop ----------
for level in range(0, MAX_N + 1):
    level_hash_to_id, level_val_grp = {}, {}
    for s in shapes(level):
        for ops in itertools.product(['+','*'], repeat=level):
            t = attach_ops(s, iter(ops))
            h = thash(t)
            if h in level_hash_to_id:                # duplicate within level
                continue
            global_id = expr_id
            level_hash_to_id[h] = global_id
            subtree_first_seen.setdefault(h, (global_id, level))
            # save DOT
            (IMG_DIR / f'expr_{global_id:04}.dot').write_text(to_dot(t, level))
            # value grouping
            level_val_grp.setdefault(val(t), []).append(global_id)
            expr_id += 1

    # ---------- LaTeX for this level ----------
    tex_lines = [
        r'\documentclass[10pt]{article}',
        r'\usepackage{graphicx}',
        r'\usepackage[margin=1cm]{geometry}',
        r'\begin{document}',
        rf'\section*{{Level $n={level}$ ({len(level_hash_to_id)} unique DAGs)}}',
    ]
    for v, ids in sorted(level_val_grp.items()):
        tex_lines.append(rf'\subsection*{{Value = {v} ({len(ids)} exprs)}}')
        for i in ids:
            tex_lines.append(r'\begin{minipage}[t]{0.18\linewidth}\centering')
            tex_lines.append(
                rf'\includegraphics[width=\linewidth,height=\linewidth,keepaspectratio]{{img/expr_{i:04}.pdf}}')
            tex_lines.append(r'\end{minipage}')
        tex_lines.append(r'\par\bigskip')
    tex_lines.append(r'\end{document}')
    Path(f'tex/lvl{level}.tex').write_text('\n'.join(tex_lines))

print(f'✓ total {expr_id} DAGs across levels 1..{MAX_N}')
Path('tex/index.json').write_text(json.dumps(subtree_first_seen, indent=2))

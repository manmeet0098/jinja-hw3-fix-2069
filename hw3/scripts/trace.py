# ruff: noqa: E501
"""Trace Symbols.branch_update to see how each {% if %} decides a variable's
initial load. Usage: python trace.py [case-name ...]  (default: all cases)

Prints, for every branch_update call, each branch slot's stores and its load
entry for the traced names, then the merged load the frame ends up with.
"""

import sys

import jinja2
from jinja2 import Environment
from jinja2 import idtracking
from jinja2 import meta

CASES = {
    "if-elif-else": "{% if c == 1 %}{% set x = 1 %}{% elif c == 2 %}{% set x = 2 %}"
    "{% else %}{% set x = 3 %}{% endif %}{{ x }}",
    "if-else": "{% if c %}{% set x = 1 %}{% else %}{% set x = 2 %}{% endif %}{{ x }}",
    "if-elif-elif-else": "{% if c == 1 %}{% set x = 1 %}{% elif c == 2 %}{% set x = 2 %}"
    "{% elif c == 3 %}{% set x = 3 %}{% else %}{% set x = 4 %}{% endif %}{{ x }}",
    "if-only": "{% if c %}{% set x = 1 %}{% endif %}{{ x }}",
    "if-elif-no-else": "{% if c == 1 %}{% set x = 1 %}{% elif c == 2 %}{% set x = 2 %}"
    "{% endif %}{{ x }}",
    "read-before-set-in-body": "{% if c %}{{ x.b }}{% set x = 1 %}{% elif d %}"
    "{% set x = 2 %}{% else %}{% set x = 3 %}{% endif %}{{ x }}",
    "read-before-set-in-else": "{% if c %}{% set x = 1 %}{% elif d %}{% set x = 2 %}"
    "{% else %}{{ x.b }}{% set x = 3 %}{% endif %}{{ x }}",
}

SLOT_NAMES = ["body", "elif", "else"]
depth = 0
orig_branch_update = idtracking.Symbols.branch_update
orig_visit_if = idtracking.FrameSymbolVisitor.visit_If


def fmt_load(sym, name):
    ref = sym.refs.get(name)
    if ref is None:
        return "-"
    return str(sym.loads.get(ref, "(no local load)"))


def traced_visit_if(self, node, **kwargs):
    global depth
    depth += 1
    try:
        return orig_visit_if(self, node, **kwargs)
    finally:
        depth -= 1


def traced_branch_update(self, branch_symbols):
    pad = "    " * depth
    print(
        f"{pad}branch_update called with {len(branch_symbols)} slots "
        f"(nesting depth {depth}):"
    )
    for i, b in enumerate(branch_symbols):
        slot = SLOT_NAMES[i] if len(branch_symbols) == 3 else str(i)
        print(
            f"{pad}  slot {slot:5s} stores={sorted(b.stores) or '{}'}  "
            f"load[x]={fmt_load(b, 'x')}"
        )
    orig_branch_update(self, branch_symbols)
    print(f"{pad}  => merged load[x] = {fmt_load(self, 'x')}")


idtracking.Symbols.branch_update = traced_branch_update
idtracking.FrameSymbolVisitor.visit_If = traced_visit_if

env = Environment()
print(f"jinja2 {jinja2.__version__} from {jinja2.__file__}\n")
for name in sys.argv[1:] or CASES:
    src = CASES[name]
    print(f"=== {name}\n    {src}")
    result = meta.find_undeclared_variables(env.parse(src))
    print(f"    find_undeclared_variables -> {sorted(result)}\n")

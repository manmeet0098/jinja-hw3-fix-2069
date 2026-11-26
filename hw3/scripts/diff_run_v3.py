# ruff: noqa: E501
"""v3 (adds every nested-scope read + include, and an ablated render).
Differential run: generate random if/elif/else templates (fixed seed), render
each under every combination of inputs, and record the output plus what
find_undeclared_variables reports. Run under two Jinja versions and compare
with diff_compare.py.

Usage: python diff_run.py OUT.json [N_TEMPLATES]
"""

import itertools
import json
import random
import sys

import jinja2
from jinja2 import DictLoader
from jinja2 import Environment
from jinja2 import meta

N = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
rng = random.Random(2069)

MACRO = (
    "{% macro m() %}<{{ x }}>{% endmacro %}{% macro k() %}{{ caller() }}{% endmacro %}"
)
NESTED_READS = [
    "{{ m() }}",
    "{% call k() %}({{ x }}){% endcall %}",
    "{% for j in [1] %}({{ x }}){% endfor %}",
    "{% with %}({{ x }}){% endwith %}",
    "{% filter upper %}({{ x }}){% endfilter %}",
]
INCLUDE = "{% include 'inc' %}"
PREFIXES = ["", "{{ x }}", "{% set x = 0 %}", INCLUDE, *NESTED_READS]
TESTS = ["c1", "c2", "c3", "x"]
BODIES = [
    "",
    "{% set x = 1 %}",
    "{{ x }}{% set x = 2 %}",
    "{% set x = 3 %}{{ x }}",
    "{% set x = x ~ 'a' %}",
    "{% set x, y = 4, 5 %}",
    "{% set x %}b{% endset %}",
    "{% if c2 %}{% set x = 6 %}{% else %}{% set x = 7 %}{% endif %}",
    "{% if c3 %}{% set x = 8 %}{% endif %}",
    "{% if c2 %}{% set x = 9 %}{% elif c3 %}{{ x }}{% set x = 10 %}"
    "{% else %}{% set x = 11 %}{% endif %}",
    "{% with %}{% set x = 12 %}{% endwith %}",
    "{{ m() }}{% set x = 13 %}",
    "{% for j in [1] %}({{ x }}){% endfor %}{% set x = 14 %}",
    "{% with %}({{ x }}){% endwith %}{% set x = 15 %}",
    INCLUDE + "{% set x = 16 %}",
]
SUFFIXES = ["{{ x }}", "{{ x }}{{ m() }}", "{{ m() }}", INCLUDE]


def gen_template():
    n_elif = rng.randint(0, 2)
    has_else = rng.random() < 0.7
    parts = [MACRO, rng.choice(PREFIXES)]
    parts.append(f"{{% if {rng.choice(TESTS)} %}}{rng.choice(BODIES)}")
    for _ in range(n_elif):
        parts.append(f"{{% elif {rng.choice(TESTS)} %}}{rng.choice(BODIES)}")
    if has_else:
        parts.append(f"{{% else %}}{rng.choice(BODIES)}")
    parts.append("{% endif %}")
    parts.append(rng.choice(SUFFIXES))
    # optionally wrap in a for loop to exercise nested frames (alias loads)
    # (v2 fix: v1 dropped the macro definition here, so m() was undefined)
    if rng.random() < 0.25:
        return MACRO + "{% for i in [1] %}" + "".join(parts[1:]) + "{% endfor %}"
    return "".join(parts)


env = Environment(loader=DictLoader({"inc": "|{{ x }}|"}))


def ablate(src):
    for r in NESTED_READS:
        src = src.replace(r, "")
    return src


def render_all(src):
    tmpl = env.from_string(src)
    renders = {}
    for c1, c2, c3 in itertools.product([True, False], repeat=3):
        for xval in (None, "CTX"):
            ctx = {"c1": c1, "c2": c2, "c3": c3}
            if xval is not None:
                ctx["x"] = xval
            key = f"{int(c1)}{int(c2)}{int(c3)}{'x' if xval else '-'}"
            try:
                renders[key] = tmpl.render(ctx)
            except Exception as e:  # record errors as output
                renders[key] = f"ERR {type(e).__name__}: {e}"
    return renders


templates = sorted({gen_template() for _ in range(N)})
results = {}
for src in templates:
    renders = render_all(src)
    ablated = render_all(ablate(src))
    undeclared = sorted(meta.find_undeclared_variables(env.parse(src)))
    results[src] = {"renders": renders, "ablated": ablated, "undeclared": undeclared}

with open(sys.argv[1], "w") as f:
    json.dump({"jinja": jinja2.__file__, "results": results}, f, indent=0)
print(f"{jinja2.__file__}: {len(templates)} unique templates x 16 contexts")

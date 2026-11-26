# ruff: noqa: E501
from jinja2 import Environment
from jinja2 import meta

env = Environment()
cases = {
    "issue: if/elif/else, set in all": "{% if c == 1 %}{% set x = 1 %}{% elif c == 2 %}{% set x = 2 %}{% else %}{% set x = 3 %}{% endif %}{{ x }}",
    "if/else, set in both": "{% if c %}{% set x = 1 %}{% else %}{% set x = 2 %}{% endif %}{{ x }}",
    "if/elif/elif/else, set in all": "{% if c == 1 %}{% set x = 1 %}{% elif c == 2 %}{% set x = 2 %}{% elif c == 3 %}{% set x = 3 %}{% else %}{% set x = 4 %}{% endif %}{{ x }}",
    "if only (no else) -> x SHOULD be undeclared": "{% if c %}{% set x = 1 %}{% endif %}{{ x }}",
    "if/elif, no else -> x SHOULD be undeclared": "{% if c == 1 %}{% set x = 1 %}{% elif c == 2 %}{% set x = 2 %}{% endif %}{{ x }}",
    "#1253: read x before set in a branch -> x SHOULD be undeclared": "{% if c %}{{ x.b }}{% set x = 1 %}{% elif d %}{% set x = 2 %}{% else %}{% set x = 3 %}{% endif %}{{ x }}",
    "plain set (control)": "{% set x = 1 %}{{ x }}",
}
for name, src in cases.items():
    print(f"{name:65s} -> {sorted(meta.find_undeclared_variables(env.parse(src)))}")

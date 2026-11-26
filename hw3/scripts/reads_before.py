# ruff: noqa: E501
"""Render: x is read BEFORE an if/else that sets x in both branches, through
each kind of nested scope. Compare with the same read before a plain set.
Rendered with c=True and x='CTX' in the context."""

import jinja2
from jinja2 import DictLoader
from jinja2 import Environment

READS = {
    "direct {{ x }}": "{{ x }}",
    "macro call": "{% macro m() %}{{ x }}{% endmacro %}{{ m() }}",
    "call block": "{% macro k() %}{{ caller() }}{% endmacro %}{% call k() %}{{ x }}{% endcall %}",
    "for loop body": "{% for i in [1] %}{{ x }}{% endfor %}",
    "with block": "{% with %}{{ x }}{% endwith %}",
    "filter block": "{% filter upper %}{{ x }}{% endfilter %}",
    "include": "{% include 'inc' %}",
    "import with context": "{% import 'mac' as h with context %}{{ h.show() }}",
    "block": "{% block b %}{{ x }}{% endblock %}",
}
ASSIGN = {
    "plain set": "{% set x = 'set' %}",
    "if/else set": "{% if c %}{% set x = 'set' %}{% else %}{% set x = 'set' %}{% endif %}",
}
env = Environment(
    loader=DictLoader(
        {"inc": "{{ x }}", "mac": "{% macro show() %}{{ x }}{% endmacro %}"}
    )
)
print(f"jinja2 from ...{jinja2.__file__[-45:]}")
print(f"  {'read before assignment':22s} {'plain set':>12s} {'if/else set':>12s}")
for rname, read in READS.items():
    row = []
    for _aname, assign in ASSIGN.items():
        out = env.from_string("[" + read + "]" + assign).render(c=True, x="CTX")
        row.append(out.split("]")[0] + "]")
    flag = "  <- differs from plain set" if row[0] != row[1] else ""
    print(f"  {rname:22s} {row[0]:>12s} {row[1]:>12s}{flag}")

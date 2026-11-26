# ruff: noqa: E501
"""find_undeclared_variables for an if/else that sets x in both branches,
placed in every kind of scope Jinja has. x should never be reported."""

import jinja2
from jinja2 import DictLoader
from jinja2 import Environment
from jinja2 import meta

IFELSE = "{% if c %}{% set x = 1 %}{% else %}{% set x = 2 %}{% endif %}{{ x }}"
CASES = {
    "top level": IFELSE,
    "for body": "{% for i in s %}" + IFELSE + "{% endfor %}",
    "for else": "{% for i in s %}{% else %}" + IFELSE + "{% endfor %}",
    "for with filter test": "{% for i in s if i %}" + IFELSE + "{% endfor %}",
    "macro": "{% macro m() %}" + IFELSE + "{% endmacro %}",
    "call block": "{% macro m() %}{{ caller() }}{% endmacro %}{% call m() %}"
    + IFELSE
    + "{% endcall %}",
    "filter block": "{% filter upper %}" + IFELSE + "{% endfilter %}",
    "with block": "{% with a = 1 %}" + IFELSE + "{% endwith %}",
    "set block body": "{% set y %}" + IFELSE + "{% endset %}",
    "block": "{% block b %}" + IFELSE + "{% endblock %}",
    "scoped block": "{% block b scoped %}" + IFELSE + "{% endblock %}",
    "child template block": "{% extends 'base' %}{% block b %}"
    + IFELSE
    + "{% endblock %}",
    "autoescape block": "{% autoescape true %}" + IFELSE + "{% endautoescape %}",
    "nested 3 levels": "{% if c %}{% if d %}{% if e %}{% set x = 1 %}{% else %}{% set x = 2 %}{% endif %}{% else %}{% set x = 3 %}{% endif %}{% else %}{% set x = 4 %}{% endif %}{{ x }}",
    "if inside elif": "{% if c %}{% set x = 1 %}{% elif d %}{% if e %}{% set x = 2 %}{% else %}{% set x = 3 %}{% endif %}{% else %}{% set x = 4 %}{% endif %}{{ x }}",
}
loader = DictLoader({"base": "{% block b %}{% endblock %}"})
print(f"jinja2 from ...{jinja2.__file__[-45:]}")
for env_name, env in (
    ("sync", Environment(loader=loader)),
    ("async", Environment(loader=loader, enable_async=True)),
):
    bad = []
    for name, src in CASES.items():
        got = meta.find_undeclared_variables(env.parse(src))
        if "x" in got:
            bad.append(f"{name} -> {sorted(got)}")
    print(f"  {env_name}: x wrongly reported in {len(bad)}/{len(CASES)} contexts")
    for b in bad:
        print("     ", b)

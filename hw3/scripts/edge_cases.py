# ruff: noqa: E501
"""Edge cases for find_undeclared_variables around {% if %} assignment.
Each case lists the CORRECT answer (worked out from Jinja's runtime semantics).
Usage: python edge_cases.py
"""

import jinja2
from jinja2 import Environment
from jinja2 import meta

env = Environment(extensions=["jinja2.ext.loopcontrols"])

# (name, template, correct set of undeclared variables, why)
CASES = [
    (
        "read before the if",
        "{{ x }}{% if c %}{% set x = 1 %}{% else %}"
        "{% set x = 2 %}{% endif %}{{ x }}",
        {"c", "x"},
        "first {{ x }} reads context",
    ),
    (
        "if-test reads x",
        "{% if x %}{% set x = 1 %}{% else %}{% set x = 2 %}" "{% endif %}{{ x }}",
        {"x"},
        "test runs before any branch",
    ),
    (
        "elif-test reads x set in body",
        "{% if c %}{% set x = 1 %}{% elif x %}"
        "{% set x = 2 %}{% else %}{% set x = 3 %}{% endif %}{{ x }}",
        {"c", "x"},
        "elif test runs when body did not",
    ),
    (
        "self-referential set",
        "{% if c %}{% set x = x + 1 %}{% else %}{% set x = 0 %}" "{% endif %}{{ x }}",
        {"c", "x"},
        "x + 1 reads context",
    ),
    (
        "different vars per branch",
        "{% if c %}{% set x = 1 %}{% else %}{% set y = 2 %}"
        "{% endif %}{{ x }}{{ y }}",
        {"c", "x", "y"},
        "each may be unset",
    ),
    (
        "read after set inside branch",
        "{% if c %}{% set x = 1 %}{{ x }}{% else %}"
        "{% set x = 2 %}{% endif %}{{ x }}",
        {"c"},
        "always set before read",
    ),
    (
        "set block form",
        "{% if c %}{% set x %}a{% endset %}{% else %}"
        "{% set x %}b{% endset %}{% endif %}{{ x }}",
        {"c"},
        "AssignBlock stores x",
    ),
    (
        "tuple unpacking",
        "{% if c %}{% set x, y = 1, 2 %}{% else %}"
        "{% set x, y = 3, 4 %}{% endif %}{{ x }}{{ y }}",
        {"c"},
        "both always set",
    ),
    (
        "import in all branches",
        "{% if c %}{% import 'a' as m %}{% else %}"
        "{% import 'b' as m %}{% endif %}{{ m }}",
        {"c"},
        "m always set",
    ),
    (
        "macro in all branches",
        "{% if c %}{% macro m() %}a{% endmacro %}{% else %}"
        "{% macro m() %}b{% endmacro %}{% endif %}{{ m() }}",
        {"c"},
        "m always set",
    ),
    (
        "set inside with (scoped)",
        "{% if c %}{% with %}{% set x = 1 %}{% endwith %}"
        "{% else %}{% set x = 2 %}{% endif %}{{ x }}",
        {"c", "x"},
        "with-scoped set does not leak",
    ),
    (
        "nested if, inner partial",
        "{% if c %}{% if d %}{% set x = 1 %}{% endif %}"
        "{% else %}{% set x = 2 %}{% endif %}{{ x }}",
        {"c", "d", "x"},
        "c true, d false leaves x unset",
    ),
    (
        "in for loop, outer x exists",
        "{% set x = 0 %}{% for i in s %}{% if c %}"
        "{% set x = 1 %}{% else %}{% set x = 2 %}{% endif %}{{ x }}{% endfor %}",
        {"c", "s"},
        "x is local/aliased, never context",
    ),
    (
        "continue in else (limitation)",
        "{% for i in s %}{% if c %}{% set x = 1 %}"
        "{% else %}{% continue %}{% endif %}{{ x }}{% endfor %}",
        {"c", "s"},
        "else leaves the iteration, so x is always set when read",
    ),
]

print(f"jinja2 {jinja2.__version__}")
for name, src, correct, why in CASES:
    got = meta.find_undeclared_variables(env.parse(src))
    mark = "ok " if got == correct else "BAD"
    print(f"  {mark} {name:32s} got={sorted(got)} correct={sorted(correct)}  ({why})")

# ruff: noqa: E501
"""Does find_undeclared_variables report names read only inside an included
template? Render with x absent / x='CTX' to show whether x is read."""

import jinja2
from jinja2 import DictLoader
from jinja2 import Environment
from jinja2 import meta

env = Environment(loader=DictLoader({"inc": "|{{ x }}|"}))
CASES = {
    "include alone": "{% include 'inc' %}",
    "include, then plain set": "{% include 'inc' %}{% set x = 1 %}{{ x }}",
    "include, then if-only set": "{% include 'inc' %}{% if c %}{% set x = 1 %}{% endif %}{{ x }}",
    "include, then if/else set": "{% include 'inc' %}{% if c %}{% set x = 1 %}{% else %}{% set x = 2 %}{% endif %}{{ x }}",
}
print(f"jinja2 from ...{jinja2.__file__[-45:]}")
for name, src in CASES.items():
    t = env.from_string(src)
    print(
        f"  {name:28s} render x absent={t.render(c=True)!r:10s} x=CTX={t.render(c=True, x='CTX')!r:12s} meta={sorted(meta.find_undeclared_variables(env.parse(src)))}"
    )

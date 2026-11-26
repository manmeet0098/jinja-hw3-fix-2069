# ruff: noqa: E501
import jinja2
from jinja2 import Environment

src = "{% if c %}{% set x = 1 %}{% elif x %}{% set x = 2 %}{% else %}{% set x = 3 %}{% endif %}{{ x }}"
out = Environment().from_string(src).render(c=False, x=True)
print(
    f"jinja2 {jinja2.__version__}: render(c=False, x=True) -> {out!r}  (correct: '2', elif x is true)"
)

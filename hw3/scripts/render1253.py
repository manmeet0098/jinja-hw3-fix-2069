# ruff: noqa: E501
import jinja2
from jinja2 import Environment

env = Environment()
print(f"jinja2 {jinja2.__version__}")
cases = {
    # template from 3.1.6's tests/test_regression.py::test_load_parameter_when_set_in_all_if_branches
    "read-in-body (regression test)": "{% if True %}{{ a.b }}{% set a = 1 %}{% elif False %}{% set a = 2 %}{% else %}{% set a = 3 %}{% endif %}{{ a }}",
    "read-in-else (same, moved)": "{% if False %}{% set a = 1 %}{% elif False %}{% set a = 2 %}{% else %}{{ a.b }}{% set a = 3 %}{% endif %}{{ a }}",
}
for name, src in cases.items():
    try:
        out = repr(env.from_string(src).render(a={"b": 0}))
    except Exception as e:
        out = f"{type(e).__name__}: {e}"
    print(f"  {name:32s} render(a={{'b': 0}}) -> {out}   (expected '01' / '03')")

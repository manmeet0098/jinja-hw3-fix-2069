# HW3: Fixing `meta.find_undeclared_variables` for variables set in every `if` branch

This repository is a copy of [pallets/jinja](https://github.com/pallets/jinja)
at **Jinja 3.1.6** with a fix for
[pallets/jinja#2069](https://github.com/pallets/jinja/issues/2069), made for a
course assignment. It was not submitted upstream. Issue numbers like `#1253`
and `#2069` in commit messages and `CHANGES.rst` refer to pallets/jinja.

The original Jinja README follows [below](#jinja).

## The bug

`meta.find_undeclared_variables()` returns the names a template may look up
from the context. In 3.1.6 it also returns a name that is set in **every**
branch of an `if` block, so it can never come from the context:

```python
from jinja2 import Environment, meta

env = Environment()
ast = env.parse(
    "{% if c == 1 %}{% set x = 1 %}{% elif c == 2 %}{% set x = 2 %}"
    "{% else %}{% set x = 3 %}{% endif %}{{ x }}"
)
meta.find_undeclared_variables(ast)  # 3.1.6: {'c', 'x'}   expected: {'c'}
```

## Root cause

`find_undeclared_variables` runs the real code generator and collects every
name it would load from the context. Those loads are decided in
`src/jinja2/idtracking.py`:

1. `Symbols.branch_update` marks every name set in **any** branch of an `if`
   as loaded from the context. Since commit `66587ce9` (released in 3.1.5,
   the fix for #1253) it never checks whether every branch sets it.
2. `FrameSymbolVisitor.visit_If` always passed three fixed branches: body,
   **all elifs together** (visited one after another as nested `if`s), and
   else (even when there is no else). So "set in all three" could not mean
   "set on every path": `if`/`else` failed even in 3.1.4, and each elif
   looked like a partial assignment.
3. Before 3.1.5, branch results were merged with `dict.update`, so the last
   branch won. A later branch could hide that an earlier branch reads the
   name before setting it. This caused #1253 (a crash) and a silent
   wrong-output bug when an `elif` test reads the name. Commit `66587ce9`
   fixed the crash by removing the "set in all branches" check instead.

## The fix (`src/jinja2/idtracking.py`, commit `10dfcba5`)

- `visit_If` passes one branch per real path: the body, each elif (its test
  and body) separately, and the else branch, which is always added (an
  empty else is the path where no test matches).
- `branch_update` counts how many branches set each new name. It skips the
  context load only if every branch sets the name **and** no branch needs
  the value from before the `if` (no branch loads it before setting it).

A name set in every branch is now treated like a name set by a plain
`{% set %}` outside the `if`. This changes rendering in one case: when the
name is also read inside a nested scope (a macro or call block called
before the `if`, or a `for`, `with` or `filter` block before it) and the
name is in the render context. That read now sees the same value as with a
plain `{% set %}` (undefined) instead of the context value. This is covered
by `test_set_in_all_if_branches_same_as_plain_set` and noted in
`CHANGES.rst`.

## Commits

| Commit | Content | Reproduction tests | Full suite |
|---|---|---|---|
| `15206881` | Original Jinja 3.1.6 release commit | (not present) | 909 passed |
| `1fc198f1` | Add reproduction tests | **2 failed** | 2 failed, 909 passed |
| `10dfcba5` | Fix + `CHANGES.rst` entry | **2 passed** | 911 passed |
| `02b0c215` | Additional tests (meta, symbol tracking, rendering) | 2 passed | 945 passed |
| latest | This README and the validation scripts in `hw3/` | 2 passed | 945 passed |

To see the whole change: `git diff 15206881 02b0c215`.

## Setup

Tested with Python 3.11, 3.12 and 3.13 on macOS.

```bash
git clone https://github.com/manmeet0098/jinja-hw3-fix-2069.git hw3-jinja
cd hw3-jinja
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/tests.txt -e .
```

The editable install (`-e .`) means that checking out another commit
changes the installed Jinja too.

## Reproduce the original failure

Check out the commit that adds only the reproduction tests to 3.1.6:

```bash
git checkout 1fc198f1
pytest tests/test_api.py -k set_in_all_if_branches
```

Expected: `2 failed`, with
`AssertionError: assert {'control', 'output'} == {'control'}`.

Then go back to the fixed version:

```bash
git checkout main
pytest tests/test_api.py -k set_in_all_if_branches
```

Expected: `2 passed`.

## Run the relevant tests

```bash
pytest tests/test_api.py::TestMeta tests/test_idtracking.py tests/test_regression.py
pytest
```

Expected: the full suite reports `945 passed`.

New tests (commits `1fc198f1` and `02b0c215`):

- `tests/test_api.py::TestMeta`
  - `test_find_undeclared_variables_set_in_all_if_branches`: the
    reproduction tests (examples from the issue).
  - `test_find_undeclared_variables_if_all_branches`: set in every branch
    (not reported).
  - `test_find_undeclared_variables_if_some_branches`: set in only some
    branches (still reported).
  - `test_find_undeclared_variables_if_load_before_store`: read before being
    set (still reported).
- `tests/test_idtracking.py`: `test_if_branching_stores_all_branches`,
  `test_if_branching_load_before_store`,
  `test_if_branching_multi_scope_all_branches`.
- `tests/test_regression.py`: `test_load_parameter_when_loaded_in_elif_test`,
  `test_set_in_all_if_branches`,
  `test_set_in_all_if_branches_same_as_plain_set`.

To run the new tests against the original code, restore only the old
`idtracking.py`:

```bash
git show 15206881:src/jinja2/idtracking.py > src/jinja2/idtracking.py
pytest   # expected: 17 failed, 928 passed
git checkout -- src/jinja2/idtracking.py
```

## Validation scripts (`hw3/scripts/`)

These scripts were used for the investigation and the report. They print
results and are not part of the test suite. Run them from the repository
root. To run one against the original 3.1.6 or 3.1.4 code, extract that
source and put it first on `PYTHONPATH`:

```bash
mkdir -p /tmp/jinja-3.1.6 /tmp/jinja-3.1.4
git archive 15206881 src | tar -x -C /tmp/jinja-3.1.6
git archive dd4a8b54 src | tar -x -C /tmp/jinja-3.1.4
PYTHONPATH=/tmp/jinja-3.1.6/src python hw3/scripts/probe.py
python hw3/scripts/probe.py
```

| Script | What it shows |
|---|---|
| `probe.py` | `find_undeclared_variables` for the main `if` shapes |
| `trace.py` | Each branch's stores and loads in every `branch_update` call |
| `edge_cases.py` | 14 edge cases with their correct answers |
| `contexts.py` | The bug in 15 kinds of scope, sync and async |
| `render1253.py` | The #1253 template: crashes on 3.1.4, renders on 3.1.6 |
| `render_elif.py` | `elif` test that reads a name set in the body: wrong output on 3.1.4 |
| `reads_before.py` | Reads before the `if` compared with a plain `{% set %}` |
| `include_contract.py` | `find_undeclared_variables` never reports names read only by included templates |
| `diff_run_v3.py`, `diff_classify_v3.py` | Differential test: random templates rendered on original and patched code |
| `wrong_fixes.py` | Plausible wrong fixes and which tests catch them |

Differential test and wrong-fix check:

```bash
PYTHONPATH=/tmp/jinja-3.1.6/src python hw3/scripts/diff_run_v3.py /tmp/orig.json 8000
python hw3/scripts/diff_run_v3.py /tmp/patched.json 8000
python hw3/scripts/diff_classify_v3.py /tmp/orig.json /tmp/patched.json
python hw3/scripts/wrong_fixes.py /tmp/jinja-3.1.6/src src /tmp/variants .
```

## Known limitations

- `{% break %}` and `{% continue %}` inside a branch are not taken into
  account, so a name set in every branch that does not leave the loop is
  still reported. This was already the case before the fix.
- Reads inside macro, call block, `for`, `with` and `filter` bodies are not
  visible to the `if` analysis. This is the same as for a plain
  `{% set %}`, and it is the reason for the rendering change above.
- Conditions are not evaluated, so a branch that can never run (for example
  `{% elif a %}` after `{% if a %}`) still counts.
- Names read only inside an included template are never reported by
  `find_undeclared_variables`, before or after the fix.

---

# Jinja

Jinja is a fast, expressive, extensible templating engine. Special
placeholders in the template allow writing code similar to Python
syntax. Then the template is passed data to render the final document.

It includes:

-   Template inheritance and inclusion.
-   Define and import macros within templates.
-   HTML templates can use autoescaping to prevent XSS from untrusted
    user input.
-   A sandboxed environment can safely render untrusted templates.
-   AsyncIO support for generating templates and calling async
    functions.
-   I18N support with Babel.
-   Templates are compiled to optimized Python code just-in-time and
    cached, or can be compiled ahead-of-time.
-   Exceptions point to the correct line in templates to make debugging
    easier.
-   Extensible filters, tests, functions, and even syntax.

Jinja's philosophy is that while application logic belongs in Python if
possible, it shouldn't make the template designer's job difficult by
restricting functionality too much.


## In A Nutshell

```jinja
{% extends "base.html" %}
{% block title %}Members{% endblock %}
{% block content %}
  <ul>
  {% for user in users %}
    <li><a href="{{ user.url }}">{{ user.username }}</a></li>
  {% endfor %}
  </ul>
{% endblock %}
```

## Donate

The Pallets organization develops and supports Jinja and other popular
packages. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, [please
donate today][].

[please donate today]: https://palletsprojects.com/donate

## Contributing

See our [detailed contributing documentation][contrib] for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.

[contrib]: https://palletsprojects.com/contributing/

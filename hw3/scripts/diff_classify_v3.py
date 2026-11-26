# ruff: noqa: E501
"""Classify v3 differential results (diff_run_v3.py).

For every template whose rendering differs between ORIGINAL and PATCHED,
check the "ablated" copy (all nested-scope reads of x removed: macro call,
call block, for body, with block, filter block). If the ablated copies render
identically on both versions, the difference is caused only by a nested-scope
read before the assignment (the documented behaviour change).

Usage: python diff_classify_v3.py ORIGINAL.json PATCHED.json
"""

import collections
import json
import re
import sys

orig = json.load(open(sys.argv[1]))["results"]
patch = json.load(open(sys.argv[2]))["results"]
NESTED = {
    "macro call": "{{ m() }}",
    "call block": "{% call k() %}",
    "for body": "{% for j in [1] %}",
    "with block": "{% with %}({{ x }})",
    "filter block": "{% filter upper %}",
}


def x_matters(r):
    return any(r[c + "-"] != r[c + "x"] for c in {k[:3] for k in r})


diffs = [s for s in orig if orig[s]["renders"] != patch[s]["renders"]]
explained = [s for s in diffs if orig[s]["ablated"] == patch[s]["ablated"]]
unexplained = [s for s in diffs if s not in explained]
kinds = collections.Counter()
for s in diffs:
    for name, marker in NESTED.items():
        if marker in s:
            kinds[name] += 1

print(f"templates: {len(orig)} (16 inputs each)")
for label, data in (("original", orig), ("patched", patch)):
    unsound = sum(
        x_matters(r["renders"]) and "x" not in r["undeclared"] for r in data.values()
    )
    imprecise = sum(
        "x" in r["undeclared"] and not x_matters(r["renders"]) for r in data.values()
    )
    print(
        f"  {label:9s} unsound (x read, not reported): {unsound:4d} | "
        f"imprecise (x reported, never read): {imprecise}"
    )
removed = [
    s
    for s in orig
    if "x" in orig[s]["undeclared"] and "x" not in patch[s]["undeclared"]
]
added = [
    s
    for s in orig
    if "x" not in orig[s]["undeclared"] and "x" in patch[s]["undeclared"]
]
print(
    f"x no longer reported: {len(removed)} (x affects patched output in "
    f"{sum(x_matters(patch[s]['renders']) for s in removed)}); newly reported: {len(added)}"
)
print(f"\nrender differences: {len(diffs)}")
print(f"  explained by nested-scope reads (ablated copies identical): {len(explained)}")
print(f"  UNEXPLAINED: {len(unexplained)}")
for s in unexplained[:10]:
    print("     ", s)
print(
    "  nested-scope readers present in differing templates (a template can have several):"
)
for k, v in kinds.most_common():
    print(f"     {v:4d}  {k}")
print(
    "  include present in differing templates:",
    sum("{% include 'inc' %}" in s for s in diffs),
    "| include-only (no nested reader):",
    sum(
        "{% include 'inc' %}" in s and not any(m in s for m in NESTED.values())
        for s in diffs
    ),
)
ex = [s for s in explained if re.search(r"\{% (for j|with %\}\(|filter|call)", s)][:3]
for s in ex:
    k = next(
        k for k in orig[s]["renders"] if orig[s]["renders"][k] != patch[s]["renders"][k]
    )
    print(
        f"  e.g. {s}\n       input {k}: original={orig[s]['renders'][k]!r} patched={patch[s]['renders'][k]!r}"
    )

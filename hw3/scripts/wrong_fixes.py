# ruff: noqa: E501
"""Build plausible-but-wrong variants of the fix in scratch copies of the
ORIGINAL 3.1.6 source, run the patched test suite against each, and report
which tests catch them. Shows (1) every part of the real patch is needed and
(2) the new tests reject naive fixes.

Usage: python wrong_fixes.py ORIG_SRC_DIR PATCHED_SRC_DIR SCRATCH_DIR REPO_DIR
"""

import shutil
import subprocess
import sys
from pathlib import Path

orig_src, patched_src, scratch, repo = map(Path, sys.argv[1:5])
orig = (orig_src / "jinja2/idtracking.py").read_text()
patched = (patched_src / "jinja2/idtracking.py").read_text()

OLD_LOOP = """        for name in stores:
            target = self.find_ref(name)
            assert target is not None, "should not happen"
"""

# The 3.1.4 version of branch_update (commit 66587ce9 reverted).
OLD_BRANCH_UPDATE_314 = """        stores: t.Dict[str, int] = {}
        for branch in branch_symbols:
            for target in branch.stores:
                if target in self.stores:
                    continue
                stores[target] = stores.get(target, 0) + 1

        for sym in branch_symbols:
            self.refs.update(sym.refs)
            self.loads.update(sym.loads)
            self.stores.update(sym.stores)

        for name, branch_count in stores.items():
            if branch_count == len(branch_symbols):
                continue

            target = self.find_ref(name)
            assert target is not None, "should not happen"
"""
ORIG_HEAD = """        stores: t.Set[str] = set()

        for branch in branch_symbols:
            stores.update(branch.stores)

        stores.difference_update(self.stores)

        for sym in branch_symbols:
            self.refs.update(sym.refs)
            self.loads.update(sym.loads)
            self.stores.update(sym.stores)

        for name in stores:
            target = self.find_ref(name)
            assert target is not None, "should not happen"
"""
RESOLVE_CHECK = """ and not any(
                sym.loads.get(target, (None, None))[0] == VAR_LOAD_RESOLVE
                for sym in branch_symbols
            )"""
NEW_VISIT_IF_START = "        # Each elif is its own branch"
ORIG_VISIT_IF = """        body_symbols = inner_visit(node.body)
        elif_symbols = inner_visit(node.elif_)
        else_symbols = inner_visit(node.else_ or ())
        self.symbols.branch_update([body_symbols, elif_symbols, else_symbols])
"""


def patched_with_orig_visit_if():
    start = patched.index(NEW_VISIT_IF_START)
    end = patched.index("    def visit_Macro")
    return patched[:start] + ORIG_VISIT_IF + "\n" + patched[end:]


VARIANTS = {
    "A: revert 66587ce9 (3.1.4 branch_update)": orig.replace(
        ORIG_HEAD, OLD_BRANCH_UPDATE_314
    ),
    "B: never force resolve (suppress in all ifs)": orig.replace(
        OLD_LOOP, OLD_LOOP + "            continue\n"
    ),
    "C: real patch minus the load-before-store check": patched.replace(
        RESOLVE_CHECK, ""
    ),
    "D: real patch minus the visit_If change (3 slots)": patched_with_orig_visit_if(),
    "E: the real patch (control)": patched,
}

for name, source in VARIANTS.items():
    assert source != orig or name.startswith("E"), f"variant {name} did not apply"
    d = scratch / ("variant_" + name[0])
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(orig_src, d / "src")
    (d / "src/jinja2/idtracking.py").write_text(source)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-rf",
            "-p",
            "no:cacheprovider",
            "tests/test_api.py::TestMeta",
            "tests/test_idtracking.py",
            "tests/test_regression.py",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(d / "src"), "PATH": "/usr/bin:/bin"},
    )
    lines = proc.stdout.splitlines()
    failed = [
        ln.split("::", 1)[1].split(" - ")[0] for ln in lines if ln.startswith("FAILED")
    ]
    print(f"{name}\n    {lines[-1]}")
    for f in failed:
        print(f"      FAILED {f}")

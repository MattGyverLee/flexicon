#
#   test_unbracketed_mutations.py
#
#   Class: TestUnbracketedMutationRatchet
#          B2g ratchet guard for decision D5 (specs/write-path-transactions/
#          tasks.md): every unbracketed LCM mutator under flexicon/code/
#          must be bracketed in a ``with self._TransactionCM(...)`` block,
#          294 sites total per the cycle-1 sweep
#          (reviews/cycle1-explore-b2sweep.md). This test makes that
#          mechanically enforceable rather than a matter of reviewer
#          diligence across ~60 files and many future spurts.
#
#   Platform: Python 3.8+
#   Copyright 2026
#

"""
Ratchet test for the write-path-transactions B2 sweep.

Two failure modes, by design:

  1. **A new (unbaselined) unbracketed method appears.** Either a genuinely
     new mutator was added without a ``with self._TransactionCM(...)``
     block, or an existing bracketed method regressed (its bracket was
     removed/narrowed). Either way this is a real, unreviewed violation of
     D5 and must fail CI.

  2. **A baselined method is no longer unbracketed.** This is the *good*
     direction -- a B2 batch landed and bracketed some methods -- but the
     baseline snapshot is a frozen artifact, so it must be edited by hand
     to drop the now-fixed entries. Silently letting the baseline overshoot
     reality would let the count quietly stop shrinking (or let someone
     re-introduce the exact same site unbracketed without CI noticing,
     since it would just "match" a stale baseline entry). Forcing the edit
     is what makes the 294 -> 0 countdown auditable batch by batch.

Net effect: the number in the baseline can only go down, and only by
someone deliberately re-running the scanner and re-freezing it -- see
``regenerate_baseline()`` docstring below.

**Status: the countdown is finished.** B2 batch 11/11 (Lexicon) took the
baseline to 0, so failure mode 2 can no longer fire and failure mode 1 is
now the permanent guard: with an empty baseline, *any* unbracketed LCM
mutator anywhere under ``flexicon/code/`` is a new violation and fails CI.
That is the steady state -- these tests are not scaffolding to remove.
"""

import ast
import json
from pathlib import Path

import pytest

from tests.write_path_transactions.scan_unbracketed_mutations import (
    CODE_ROOT,
    _iter_source_files,
    _scan_method,
    scan,
)

BASELINE_PATH = Path(__file__).parent / "snapshots" / "unbracketed_baseline.json"


def _load_baseline():
    if not BASELINE_PATH.exists():
        pytest.fail(
            f"No baseline found at {BASELINE_PATH}. Generate one with:\n"
            "  python -m tests.write_path_transactions.scan_unbracketed_mutations "
            f"--baseline {BASELINE_PATH}"
        )
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _key(entry):
    """Identity for baseline comparison: (file, class, method). Line number
    is deliberately excluded -- it drifts whenever unrelated code above a
    method is edited, and the ratchet must not fire on line-number churn
    alone."""
    return (entry["file"], entry["class_name"], entry["method_name"])


def _how_to_fix(entry):
    return (
        f'wrap {entry["file"]}:{entry["line"]} '
        f'{entry["class_name"]}.{entry["method_name"]} in '
        f'`with self._TransactionCM("<label>"):` and remove its entry from '
        f"{BASELINE_PATH.name}"
    )


class TestUnbracketedMutationRatchet:
    def test_scanner_is_functional(self):
        """Sanity check that the scanner still WORKS, now that a zero result
        is the correct answer.

        Until B2 landed, this test asserted ``len(scan()) > 0`` -- an empty
        result then meant the scanner was broken (walking the wrong
        directory), because real violations were known to exist. B2 batch
        11/11 took the count to zero, so that assertion inverted: it would
        now fail precisely because the sweep succeeded.

        The ratchet tests below are NOT deleted -- with a zero baseline they
        become the permanent guard against any new unbracketed mutator. But
        they would also pass vacuously if the scanner silently stopped
        detecting anything, so this test pins the two properties that a
        zero-violation `scan()` no longer proves on its own:

          1. the scanner walks a real tree that actually contains source; and
          2. its detection logic still flags an unbracketed mutation, and
             still does NOT flag a bracketed one.
        """
        source_files = list(_iter_source_files())
        assert len(source_files) > 50, (
            f"Scanner walked {CODE_ROOT} and found only {len(source_files)} "
            "source file(s) -- it is almost certainly pointed at the wrong "
            "directory. A zero-violation result from this tree proves nothing."
        )

        unbracketed = ast.parse(
            "class C:\n"
            "    def m(self):\n"
            "        self.thing.OwningList.Remove(x)\n"
        ).body[0].body[0]
        assert _scan_method(unbracketed) == {".Remove"}, (
            "Scanner failed to flag a plainly unbracketed .Remove() -- its "
            "detection logic is broken, so the zero baseline is meaningless."
        )

        bracketed = ast.parse(
            "class C:\n"
            "    def m(self):\n"
            '        with self._TransactionCM("label"):\n'
            "            self.thing.OwningList.Remove(x)\n"
        ).body[0].body[0]
        assert _scan_method(bracketed) == set(), (
            "Scanner flagged a correctly bracketed mutation -- it would "
            "report false violations against a fully swept tree."
        )

    def test_no_new_unbracketed_mutations(self):
        """
        FAILS if any currently-unbracketed method is NOT in the frozen
        baseline. This is the primary guard: it catches both a brand-new
        unbracketed mutator and a regression of a previously-bracketed one.
        """
        current = {_key(f.to_dict()): f.to_dict() for f in scan()}
        baseline_entries = _load_baseline()["entries"]
        baseline_keys = {_key(e) for e in baseline_entries}

        new_violations = [current[k] for k in current if k not in baseline_keys]
        if new_violations:
            new_violations.sort(key=lambda e: (e["file"], e["line"]))
            lines = [
                f"  - {e['file']}:{e['line']} {e['class_name']}.{e['method_name']} "
                f"[{', '.join(e['kinds'])}] -- {_how_to_fix(e)}"
                for e in new_violations
            ]
            pytest.fail(
                f"{len(new_violations)} NEW unbracketed LCM mutation site(s) found "
                "(not present in the frozen baseline). Every LCM mutator must run "
                'inside `with self._TransactionCM("<label>"):` per decision D5 '
                "(specs/write-path-transactions/tasks.md).\n" + "\n".join(lines)
            )

    def test_baseline_ratchets_down_as_sites_are_bracketed(self):
        """
        FAILS if the baseline lists a method that is no longer unbracketed
        (i.e. it was successfully wrapped in `with self._TransactionCM(...)`
        by a B2 batch). The baseline is a frozen snapshot, not a live
        query -- it must be edited by hand each time a batch lands, which
        is what keeps the 294 -> 0 countdown meaningful and auditable.
        """
        current_keys = {f.key for f in scan()}
        baseline_entries = _load_baseline()["entries"]

        stale = [e for e in baseline_entries if _key(e) not in current_keys]
        if stale:
            stale.sort(key=lambda e: (e["file"], e["line"]))
            lines = [
                f"  - {e['file']}:{e['line']} {e['class_name']}.{e['method_name']}"
                for e in stale
            ]
            pytest.fail(
                f"{len(stale)} baseline entr(ies) are already bracketed and must be "
                f"REMOVED from {BASELINE_PATH.name} (ratchet the baseline down -- "
                "do not leave fixed sites listed):\n" + "\n".join(lines)
            )

    def test_baseline_total_matches_entry_count(self):
        """Sanity check on the baseline artifact itself: the ``total`` field
        must match len(entries) -- guards against a hand-edited baseline
        going out of sync with its own entry list."""
        baseline = _load_baseline()
        assert baseline["total"] == len(baseline["entries"]), (
            f"Baseline 'total' ({baseline['total']}) does not match its "
            f"'entries' length ({len(baseline['entries'])}) -- {BASELINE_PATH}"
        )

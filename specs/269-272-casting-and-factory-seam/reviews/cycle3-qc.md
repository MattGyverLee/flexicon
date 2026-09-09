# Cycle 3 -- QC triage: assert-swallowing handlers in live tests

Scope: the 6 sites where a `try` body containing an `assert` has a handler
that could swallow `AssertionError`. Read-only; no files modified.

NOTE ON PROVENANCE: lex-qc is provisioned with Read/Grep/Glob only and could
not write this file. The content below is its verbatim reported finding,
persisted by the main session so it can be relayed by path.

## Prior sweep, already closed (do not redo)

An AST scan of the entire repo for `return`/`break`/`continue` inside any
`finally` body returned exactly ONE hit -- the line introduced in cycle 2 at
`tests/operations/test_collection_cast_pattern.py:1053`, since repaired. No
sibling sites, so no prior live evidence is devalued by that mechanism.

## Per-site verdicts

| Site | Handler | Assert under test | Verdict |
|---|---|---|---|
| test_allomorphs_live.py:138 | `except StopIteration: pass` | `assert first is not None` | BENIGN -- handler catches only `StopIteration` from `next()`; `AssertionError` is a different type and propagates. Empty project is a legitimate outcome. |
| test_etymologies_live.py:176 | `except StopIteration: pass` | `assert first is not None` | BENIGN -- same shape |
| test_examples_live.py:136 | `except StopIteration: pass` | `assert first is not None` | BENIGN -- same shape |
| test_pronunciations_live.py:184 | `except StopIteration: pass` | `assert first is not None` | BENIGN -- same shape |
| test_variants_live.py:197 | `except StopIteration: pass` | `assert first is not None` | BENIGN -- same shape |
| **test_wfi_analysis.py:682** | **`except Exception: pass`** | `assert leftover is None` | **HAZARD** |

## The one HAZARD

`tests/operations/test_wfi_analysis.py:682`, in
`TestWfiAnalysisDeleteWithMorphBundles.test_delete_analysis_with_morph_bundle_cascades`
(cascade-delete coverage for issues #99 / #32), lines 675-686:

```python
try:
    leftover = writable_project.Object(bundle_hvo)
    assert leftover is None, (
        "WfiMorphBundle survived deletion of its owning "
        "analysis -- cascade delete did not fire. ..."
    )
except Exception:
    # Any exception from Object() also means the bundle is gone ...
    pass
```

`except Exception` is a superclass of `AssertionError`. If the cascade delete
genuinely fails to remove the `WfiMorphBundle`, `leftover is not None`, the
assert raises, and the handler -- intended only to absorb a lookup failure
from `Object()` -- silently swallows it. The claim lost is precisely the one
the test exists to prove: that deleting an owning `WfiAnalysis` cascades to
its `WfiMorphBundle` children. The test can report green with cascade delete
broken.

## Does any recorded live evidence rest on the HAZARD site?

**No.** A search of `specs/*/evidence/` found no file referencing
`test_delete_analysis_with_morph_bundle_cascades` or "cascade delete" by name.
`specs/write-path-transactions/evidence/live-def-default-flip.md:199` does list
`test_wfi_analysis.py` under a harness-fix table, but cites a different site
(`SetEvaluation` x2, `MorphBundlesOS.Add` -- an `UndoableOperation` wrapping fix
around line 653), unrelated to the swallowed assertion at 682.

## Recommended fix shape (not implemented)

Restructure so the assert sits OUTSIDE the `try`: call `Object()` in the try,
capture the result or a sentinel/exception flag, then assert after the block.
Alternatively narrow the handler to the specific exception pythonnet surfaces
for a deleted HVO. Either way this is a test-integrity change to a write-path
cascade claim, so it warrants its own live verification -- at minimum
confirming the corrected assertion still fires correctly when the cascade
genuinely succeeds.

## Scope note

Out of scope for #270 -- none of the 6 sites is in the #270 file. The HAZARD
is a pre-existing test-integrity defect worth its own tracked issue.

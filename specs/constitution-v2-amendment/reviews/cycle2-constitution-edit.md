# Cycle 2 — Constitution edit report

Five instructed edits applied to `.specify/memory/constitution.md`. No other
text restructured, reflowed, or improved.

## Edit 1 — Principle VII, first paragraph (keyword-arg exception)

Appended after "new exception types subclassing an existing one.":

> One exception: a new keyword argument whose default reproduces behavior
> Principle V would call a defect is not additive growth — it is a defect
> preserved behind a flag. Such an argument defaults to the corrected
> behavior, with the old path reachable only by explicit opt-in
> (`docs/API_DESIGN_PHILOSOPHY.md` rule 5).

## Edit 2 — Principle VII, "Published" definition paragraph

Inserted immediately before "**Altering or withdrawing**...":

> **Published** means a name bound in `flexicon/__init__.py`'s namespace —
> enumerated explicitly in its `__all__`, which is the single source of
> truth — together with the public methods of the classes so exported. A
> name reachable only as `flexicon.code.*` is internal regardless of
> whether it begins with an underscore, and may be renamed or removed
> freely.

## Edit 3 — Development Workflow, surface-snapshot paragraph

Appended before the final "`docs/API_SURFACE.md` maps..." sentence:

> The baseline covers statically declared names only. Attributes forwarded
> at runtime through a wrapper's `__getattr__`
> (`flexicon/code/Shared/wrapper_base.py`,
> `flexicon/code/PythonicWrapper.py`) do not exist as Python names in the
> source and cannot be enumerated from it; they are governed instead by
> the liblcm contract baseline and Principle VII's cause 1. The baseline
> tracks the `flexicon` package only — the `flexlibs2` shim's removal at
> v5.0.0 is governed by `CLAUDE.md` and
> `tests/test_flexlibs2_alias_ratchet.py`, not by this baseline.

## Edit 4 — Quality Gates item 5, final sentence

Changed to:

> Purely additive changes are exempt and need only a regenerated surface
> baseline; the forward pass never blocks a commit, only changed or
> removed entries can.

## Edit 5 — Version bump and amendment log

New entry inserted above the 2.0.0 entry, as instructed verbatim (see file,
lines 253-263). Final line updated to:

> **Version**: 2.1.0 | **Ratified**: 2026-08-14 | **Last Amended**: 2026-09-22

## Fit notes

All five edits fit the surrounding prose cleanly with no wording conflicts.
One mechanical judgment call: edit 1's instruction said "insert" after the
cited sentence without specifying paragraph placement; it was appended to
the end of the existing first paragraph (before the blank line/paragraph
break) rather than started as a new paragraph, since the instruction gave
no blank-line cue and the sentence reads as a continuation of the "Adding"
paragraph's scope. Edit 4's replacement required matching the existing
3-space continuation-line indentation under the numbered list item, which
was not shown in the instruction's literal before/after strings but was
inferred from the file's own list formatting.

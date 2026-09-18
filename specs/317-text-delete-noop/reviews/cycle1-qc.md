# QC Report -- flexicon dbabca6 (fix/317-text-delete-noop)

> Authored by the cycle-1 lex-qc agent (read-only: Read/Grep/Glob only). The agent
> had no Write tool, so the main session committed this body verbatim to the path
> the dispatch specified.

**Quality Score:** 88/100
**Status:** ISSUES (non-blocking; recommend two small follow-ups)

## Pattern-Audit Gate

CHANGELOG explicitly documents a horizontal check: the `Create()` `lp.Texts.Add()`
call was swept and found harmless (factory already registers unowned objects) and
removed. That is a one-off/local sibling sweep, not the broader multi-repo pattern
sweep the gate is built for, but the shape (unowned-collection mutation) was
checked here in the same file. Gate: PASS (justified in commit body).

## Findings

### P1 -- CI never executes the regression test on every commit

`local-compat-check.yml` (runs on every push/PR to main/develop) is pure AST/static
analysis -- it parses `.py` files for syntax and class structure but never invokes
pytest, so it cannot catch a live-DB behavioral regression. The only workflow that
actually runs `pytest tests/ -v --tb=short` is `upstream-compatibility-check.yml`,
which is `schedule: cron '0 9 * * 1'` (weekly) or manual `workflow_dispatch`, on a
self-hosted Windows+FieldWorks runner -- not on PRs. `test_delete_actually_removes_the_text`
(test_text_operations.py:304) and its sibling `test_create_and_delete_text` (:277)
are also missing `@pytest.mark.requires_live_project` (only `@pytest.mark.integration`
is applied at the class level, plus the metadata-only `live_phase` marker) -- but this
doesn't matter for CI gating since the weekly job runs unfiltered `pytest tests/`
either way. **Net effect: a re-regression of `Delete()` would ship silently through
every PR and only surface up to a week later on the scheduled run**, exactly the
failure mode the PR is fixing. Recommend either (a) a mock-mode unit test that
patches `IText.Delete` / verifies it's called (protects the code path in fast CI),
or (b) adding a nightly-run gate/status check that blocks merge if it later goes red.

### P1 -- Existing sibling tests are blind to this exact bug class

`test_has_delete_method` (test_text_operations.py:99) only asserts
`callable(ops.Delete)` -- would pass against the old no-op forever. Before this
commit, `test_create_and_delete_text` (:277) also asserted only "did not raise" (a
missing `text` object reference and a title check on the object still held in
Python, not a re-query) -- it could not have caught the bug either, since the stale
Python object still answers `GetTitle` correctly after a no-op delete. This is
exactly the "every does-it-raise test passed against it" observation the new
test's own docstring (test_text_operations.py:312) calls out -- good self-awareness,
but worth flagging as a still-open gap on the *other* Operations classes using the
same unowned-collection idiom (WordformOperations is cited as already correct;
others weren't audited here).

### P2 -- Stale-cleanup preamble produces a confusing failure mode under regression

test_text_operations.py:322-327: if `Delete()` regresses to a no-op again AND a
stale `"Test Text 317 Delete Effect"` object is left over from a prior run, the
preamble's own `ops.Delete(stale)` silently no-ops, `Exists(name)` stays True, and
the subsequent `ops.Create(name)` (line 330) raises `FP_ParameterError: already
exists` instead of failing on the intended assertion at line 336. The test still
fails (no false green), but the failure message misleads whoever reads it toward
"duplicate name" rather than "Delete() is broken." Low severity since it doesn't
create a false pass, but consider asserting `not ops.Exists(name)` right after the
stale-cleanup block, before computing `before`, so a regression reports at the
right line.

### Comment-orphan / dead-call check -- Create()/Duplicate() -- PASS

`Create()` (TextOperations.py:175-201): the removed `lp.Texts.Add(new_text)` is
replaced by a comment block (:180-185) that reads as an explanation, not an orphan
-- it cites #317 and #22 and states the factory already registers the object.
Nothing downstream in `Create()` re-reads `lp.Texts` or depends on the object being
in that list; `new_text` is returned directly and used by callers/`Duplicate()` via
its return value only. `Duplicate()` (:243-344) calls `self.Create()` and never
touches `lp.Texts` -- confirmed no dependency. Reads cleanly.

### Delete() error handling -- PASS

`Delete()` (TextOperations.py:204-240): calls `_EnsureWriteEnabled()` first (raises
`FP_ReadOnlyError` correctly), then `__GetTextObject()` which raises
`FP_NullParameterError`/`FP_ParameterError` on bad input via `_ValidateParam` and the
HVO/ClassName-cast logic (:94-115). `IText(obj)` casting is the same pattern already
proven in `GetName`/`SetName`/etc. -- `.Delete()` is an `ICmObject` method so it's
callable on any `IText`-cast object without further casting. One gap: **if the text
was already deleted (stale HVO)**, `self.project.Object(hvo)` inside `__GetTextObject`
is the failure point -- behavior there (does it raise `FP_ParameterError` or a raw LCM
KeyNotFoundException?) is inherited from existing code, not part of this diff, so
out of scope for this review, but worth a follow-up ticket since `Delete()` is the
one place staleness is most likely to be hit in practice (double-delete in a loop).

## CHANGELOG -- PASS

Entry is accurate, correctly scoped under `[Unreleased] / Fixed`, and goes further
than most fixes by including the field report and the `Create()` sibling cleanup
in the same entry with clear reasoning. No changes needed.

## Recommendation

FIX ISSUES (both P1s) before calling this fully closed -- the code fix itself is
correct and well-documented; the gap is exclusively in verification durability.

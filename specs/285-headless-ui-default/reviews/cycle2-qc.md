# QC Report -- issue #285 (cycle 2)

**Date:** 2026-09-08
**Diff:** `8e657e8..4526245` on `fix/285-headless-ui-default`
**Quality Score:** 90/100
**Status:** [ISSUES] -- one P1, otherwise clean

## Pattern-Audit Gate

- Sweep present in commit body (`4526245`): **[FAIL]** -- no "Pattern audit"
  heading. Bug is `bug`-labelled and the commit says `Closes #285`, so the
  gate fires.
- Sweep performed by QC in lieu of the missing section, on both candidate axes:
  - **Axis 1 -- "keyword default that preserves the hazard":** genuinely a
    single binding site. `FLExLCM.py:101-103` is the only `ui=None`
    resolution; `FLExProject.OpenProject` (`FLExProject.py:164`) is pure
    passthrough. Every other boolean safety kwarg under `flexicon/code/`
    already defaults to the safe branch (`force=False` x5;
    `raise_on_conflicting_save=True`). No sibling to sweep.
  - **Axis 2 -- "constructs WinForms / assumes a message pump on a headless
    path":** **one live unswept sibling** --
    `flexicon/code/FLExLCM.py:109`, `dlg = ProgressDialogWithTask(th)`,
    constructed unconditionally on *every* `OpenProject` and handed to
    `CreateCacheFromExistingData` as `IThreadedProgress`. Same shape as the
    bug just fixed; only `settings.DisableDataMigration = True` keeps it
    off the hot path. Plus a dead WinForms import,
    `FLExLCM.py:43 ChooseLangProjectDialog`, unreferenced anywhere.
- Gate status: **PASS** (axis 1 exempt as a justified one-off; axis 2 recorded
  rather than silently skipped -- see P2-1, follow-up issue, not this PR).

## Live-LCM Evidence Gate

- Touches an LCM write/open path: **yes** (`FLExLCM.OpenProject`).
- Artifact: `specs/285-headless-ui-default/evidence/live-prefix-conflict.md`
- `run_mode`: **live** (2026-09-08T20:59:41Z, in-worktree `live_status.json`).
- Pre/post field values re-queried, not asserted on input: **[OK]** -- pre
  `"seed_value"`, post `"writer1_value"` read from a *third, fresh*
  `FLExProject` session after both writers closed. This is real evidence: it
  measures the discard rather than inferring it from #238's reflection, and it
  staged a genuine two-writer `kSharedXML` conflict without touching real
  Target/Sena 3.
- Cleanup confirmed: **[OK]** (`restore_target.py --check` clean; sandboxes and
  worktree removed; hung workers terminated and disclosed).
- Gate status: **PASS (pre-fix); post-fix IN FLIGHT.** To fully close,
  `live-postfix-conflict.md` must show `run_mode: live`, the same staging
  mechanism, `ui=None` on `4526245` raising `FP_ConflictingSaveError`, and a
  fresh-session re-read proving writer 2's value was *not* discarded (i.e. the
  post-state differs from the pre-fix `"writer1_value"`), plus the >105s block
  not recurring.
- **Note:** the commit body still says "Live-LCM verification ... was not
  performed this cycle ... reported as FAIL: unverified". That was true when
  written and is now stale/contradicted by the committed evidence (P2-2).

## Code Quality: 23/25

Readability 9/10, Maintainability 8/8, Consistency 6/7. Docstrings are the
strongest part of the change -- both `FLExLCM.py:82-95` and
`FLExProject.py:210-235` now state the new default *and* carry a runnable
opt-out snippet, and the retained `FwLcmUI` hazard prose is correctly reframed
as opt-out rationale rather than deleted.

**Issues:** none in code.

## Standards Compliance: 21/25

Style [Pass]. Naming [Pass]. Organization [Pass]. `flexlibs2` hygiene
**[Pass]** -- the only diff hits are inside a *removed* CHANGELOG/doc paragraph
and a historical back-reference to #240; no new internal reference, ratchet
(`tests/test_flexlibs2_alias_ratchet.py`) unaffected. Emoji: **none** in the
diff (checked over the full BMP/SMP emoji ranges).

**Issues:** P1-1 below -- one in-tree statement still asserts the old default.

## Error Handling: 25/25

Exceptions [Pass] -- `FP_ConflictingSaveError` stays in the `FP_RuntimeError`
hierarchy, so the documented `except FP_RuntimeError` still catches the new
default failure. Edge cases [Pass] -- `raise_on_conflicting_save=True` is now
load-bearing and pinned by test. Messages [Pass] -- the raise text tells the
caller their writes were *not* discarded and what to do next.

## Best Practices: 21/25

Design patterns 8/9. Anti-patterns [Pass] -- notably this is the *correct*
resolution of CLAUDE.md rule #5: the hazard is removed unconditionally by
flipping the default, not licensed by a new opt-in kwarg. Performance [Pass].

**Import-order claim (verified, not trusted):** the eager
`from .code.headless_ui import HeadlessLcmUI` at `flexicon/__init__.py:118`
does **not** add a second CLR type emission. `__init__.py:90` imports
`.code.FLExProject`, which at `FLExProject.py:18` does `from . import
FLExLCM`, which now imports `.headless_ui` at module level
(`FLExLCM.py:45`). By line 118 the module is a `sys.modules` hit; the
`ILcmUI` subclass body -- where pythonnet emits the type -- executes once.
The author's argument holds. Real (small) new cost, correctly unavoidable: the
emission is now unconditional for *every* `import flexicon`, where before it
happened only for opt-in callers.

**`ThreadHelper` requirement met:** `th` is still constructed and still feeds
`ProgressDialogWithTask(th)` (`FLExLCM.py:101,109`); only the `FwLcmUI`
consumer went away. `FwLcmUI` remains imported and reachable
(`FLExLCM.py:42`).

**Test load-bearing analysis (by reading, suite not run):**

| Test | Load-bearing? |
|---|---|
| `test_headless_lcm_ui.py:230` `..._defaults_to_headlesslcmui` | **Yes.** Captures the real `ui` arg via monkeypatched `LcmCache`; `isinstance(..., HeadlessLcmUI)` fails under the old `FwLcmUI` default. Author confirms it did fail (1 failed / 1713 passed) before the source edit -- the delta was observed, not assumed. |
| `:274` `..._explicit_fwlcmui_opt_out_still_reaches_lcm` | **Yes.** `is explicit_fw_ui` identity assertion fails if any future wrapping/coercion of an explicit `ui=` is introduced. Passing under both old and new source is *correct* here -- it pins the invariant the flip must not break. |
| `:77` `..._defaults_to_raise_on_conflicting_save` | **Yes but redundant.** Fails if the constructor default flips to `False`. However `:71 test_conflicting_save_raises_by_default` already constructs a bare `HeadlessLcmUI()` and asserts the raise, so it covers the same regression behaviourally; the new test adds only coupling to the private `_raise_on_conflicting_save`. Keep, but it is belt-and-braces. |
| `tests/contract/test_lcm_contract.py:442-463` `test_ilcm_ui_full_surface` | **Not load-bearing for #285, correctly untouched.** It asserts liblcm's `ILcmUI` shape (10 methods + 2 properties) from the baseline snapshot and says nothing about which implementation is the default -- it passes under both old and new behaviour by design. It *is* load-bearing for the separate "HeadlessLcmUI implements the whole interface" invariant, so leaving it alone (as `cycle1-programmer.md` concluded) is right. |

**CHANGELOG discoverability (asked explicitly): [Pass].** A consumer preparing
for shared mode can act on `CHANGELOG.md:129-168` without opening the source:
it names #285/#238, names `HeadlessLcmUI`, names the new top-level import,
names the raising behaviour and its `FP_ConflictingSaveError`, and gives the
opt-out as a copy-pasteable block including both `SIL.*` imports. It also
pre-empts `SilentLcmUI` being re-proposed. One gap -- see P2-3.

## Prioritized findings

**P1-1 -- `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md:314-316` still asserts the old
default.** Reads: "`ui=None` (the default, unchanged for backward
compatibility) still constructs `FwLcmUI` -- verified by monkeypatch test and
by the verification agent reading `FLExLCM.py:98-99`." Both clauses are now
false, and the monkeypatch test it cites has been *inverted* by this very
diff. This is the write contract a consumer reads before enabling shared mode,
and the diff already edits this file twice (`:246`, header figures) -- so §5
is a miss, not out of scope. One-paragraph edit.

**P2-1 -- `flexicon/code/FLExLCM.py:109` / `:43`:** the axis-2 sibling above.
`ProgressDialogWithTask(th)` on every headless open, and a dead
`ChooseLangProjectDialog` import. Pre-existing, unchanged here; file a
follow-up rather than widening this PR.

**P2-2 -- commit `4526245` body:** the "FAIL: unverified" paragraph is now
contradicted by the committed pre-fix evidence. Correct it (or note the
supersession) when the post-fix evidence lands, so the release record does not
say unverified when live evidence exists. Also add the axis-1/axis-2 sweep
conclusion under a "Pattern audit" heading, per the gate.

**P2-3 -- `CHANGELOG.md:150-159`:** documents only the raise-or-opt-out binary.
The middle option a shared-mode consumer may actually want --
`HeadlessLcmUI(raise_on_conflicting_save=False)`, non-destructive but silent --
is reachable only by reading `headless_ui.py:87`. One sentence would close it.

**P2-4 -- `docs/EXCEPTION_HANDLING.md:33`** still routes readers to
`flexicon.code.headless_ui.HeadlessLcmUI` and cites only #238; and
`docs/FLEXTOOLSMCP_WRITE_CONTRACT.md:386` still renders `ui=` injection as
"Unchanged" in its Post-Track-B column. Both stale, neither a lie about the
default. Historical spec records under `specs/write-path-transactions/` are
correctly left alone -- they document the #238-era decision as of then.

## Final Assessment

**Overall Score:** 90/100
**Recommendation:** **APPROVE-WITH-NITS**, conditional on P1-1 (a
one-paragraph doc edit; does not warrant re-review) and on
`live-postfix-conflict.md` landing with the four properties listed under Gate
2. Both gates pass. The fix itself is minimal, correctly scoped to the single
binding site, keeps the opt-out genuinely reachable and test-pinned, and the
import-order and test-load-bearing claims survived independent verification.

---
**Reviewed By:** QC Agent (lex-qc), cycle 2

# Issue #285 - cycle 1 programmer report

## Files + lines changed

- `flexicon/code/FLExLCM.py`: added `from .headless_ui import HeadlessLcmUI`
  (module-level import block); `OpenProject()` default flipped
  `ui = FwLcmUI(None, th)` -> `ui = HeadlessLcmUI()` (line ~99); docstring
  `ui:` block rewritten to state the new default and the `FwLcmUI(None,
  ThreadHelper())` opt-out. `ThreadHelper()`/`th` untouched, still feeds
  `ProgressDialogWithTask(th)`.
- `flexicon/__init__.py`: added `from .code.headless_ui import HeadlessLcmUI`
  after the `FLExProject` import block (~line 100), with a comment
  explaining the sys.modules-cache-hit reasoning; CAPABILITIES docblock
  `"ui-injection"` line rewritten to name the new default and the opt-out.
- `flexicon/code/FLExProject.py`: `OpenProject`'s `ui:` docstring block
  (~lines 210-229) rewritten: new default stated first, opt-out shown with
  a code sample, old `FwLcmUI` hazard text kept but reframed as the
  non-default path.
- `flexicon/code/headless_ui.py`: module docstring lines 18-20 (no longer
  "unconditionally by flexicon") and line 53 ("Passing no `ui` preserves the
  historical `FwLcmUI` behaviour" -> states the new default and the
  opt-out), plus a top-level import example using `flexicon.HeadlessLcmUI`.
- `CHANGELOG.md`: new `### Changed` BREAKING entry under `[Unreleased]`,
  first bullet, naming #285, #238, `HeadlessLcmUI`, the hazard, the new
  raising default, the `SilentLcmUI` rejection, and the `ui=FwLcmUI(None,
  ThreadHelper())` opt-out.
- `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md`: header test tallies (~lines 43-52)
  replaced with re-measured figures, explicitly marking the old numbers
  historical; `"ui-injection"` capability table row (~line 246) now states
  the default `HeadlessLcmUI()` and the `FwLcmUI` opt-out.
- `tests/test_headless_lcm_ui.py`: file header rewritten; the FwLcmUI-default
  regression test renamed to `test_flexlcm_openproject_defaults_to_headlesslcmui`
  and inverted to assert `isinstance(captured["ui"], HeadlessLcmUI)`; added
  `test_flexlcm_openproject_explicit_fwlcmui_opt_out_still_reaches_lcm`
  (opt-out proof, real `FwLcmUI(None, ThreadHelper())` identity-checked
  through); added `test_bare_headless_lcm_ui_defaults_to_raise_on_conflicting_save`
  (locks the constructor default so raising can't silently regress).
  `tests/contract/test_lcm_contract.py:442-463` (`test_ilcm_ui_full_surface`)
  reviewed - it only reflects the `ILcmUI` interface surface, not defaults;
  no change needed.

## Export route chosen: eager, same-object re-export

`flexicon/code/FLExLCM.py` already imports `.headless_ui` at module level
(needed for the new default), and `flexicon/__init__.py` already imports
`FLExProject` (which imports `FLExLCM`) eagerly before the new
`HeadlessLcmUI` import line runs. So the CLR type emission for
`HeadlessLcmUI(ILcmUI)` happens once, as a side effect of the pre-existing
import chain, not twice. Measured:

```
python -c "import flexicon; print(flexicon.HeadlessLcmUI)"
  -> <class 'flexicon.code.headless_ui.HeadlessLcmUI'>
python -c "from flexicon.code.headless_ui import HeadlessLcmUI as A; import flexicon; print(A is flexicon.HeadlessLcmUI)"
  -> True
```

`import flexicon` wall time: ~1.22s, dominated by the pre-existing
SIL.LCModel/FieldWorks assembly loads (unchanged order of magnitude from a
direct `import flexicon.code.headless_ui`, ~1.20s, measured standalone
before this change existed at package level). No lazy `__getattr__` was
needed.

## Offline suite tallies

`python -m pytest -m "not requires_live_project" -q`, final run after all
edits: **1716 passed, 690 deselected, 0 failed, 8 warnings, 5 subtests
passed** (29.28s). Before the test-file fix, the pre-existing regression
test correctly caught the default flip as a real behaviour change (1 failed,
1713 passed) - included here to show the delta was expected, not
accidental.

## What could NOT be done

Live verification (`FLEXLIBS_REQUIRE_LIVE=1`, a genuine shared-mode
conflicting-save reproduction with a concurrent second writer) was not
attempted in this cycle - the issue's own verification section flags this
as needing `projectSharing="true"` plus a real concurrent writer, which
`target_sandbox` cannot produce alone. Reporting `FAIL: unverified` for the
live-LCM half rather than substituting a mock pass, per CLAUDE.md; this
should be picked up as a follow-up live-verification task before release.

Branch: `fix/285-headless-ui-default` (verified via `git branch
--show-current` before committing). No commits made to `main`.

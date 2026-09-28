# T1b -- Breaking-Change Review: Issue #325 Syncable Properties

**Task:** T1b (lex-author breaking-change review)
**Ruling source:** specs/325-syncable-properties/rulings.md (T1 complete)
**Evidence base:** live-T0-reflection.md + live-T0-*-raw.json (run_mode=live, 6/6 passed)
**Rulings reviewed:** R1, R2, R3, R4, R5, R6, R7, R8
**Date:** 2026-09-22
**Branch:** fix/325-syncable-properties

---

## Scope note

Dispatcher decisions are binding and not re-litigated here:
- **R5 choice (a):** adopt #290 model + defer full Preposed proof to T3.
- **R4 needs_human:** MediaFilesOC vs MediaURIsOC discrepancy in `GetMediaFiles`/`AddMediaFile`
  stays open; T2c implements `media_uris` key shape only.

---

## 1. Public API Breaks

### R6 -- GetLanguage / SetLanguage on ILexEtymology (DEPRECATION + NEW METHODS)

**Affected class:** `EtymologyOperations`
**Affected callers:** Any code calling `project.Etymology.GetLanguage(...)` or
`project.Etymology.SetLanguage(...)`

| Method | Before R6 | After R6 |
|--------|-----------|----------|
| `GetLanguage(etym)` | Returns `None` (always; `LanguageRA` absent) | Returns `GetLanguages()[0]` or None; emits `[WARN]` |
| `SetLanguage(etym, lang)` | No-op (always; `LanguageRA` absent) | Calls `SetLanguages([lang])`; emits `[WARN]` |
| `GetLanguages(etym)` | Does not exist | Returns ordered `list[ICmPossibility]` |
| `SetLanguages(etym, langs)` | Does not exist | Replaces full `LanguageRS` sequence |

**Behavior break -- silent-to-functional:** Both old methods were permanently
silently broken (always no-op / always None due to nonexistent `LanguageRA`).
After R6 they will actually operate via `LanguageRS`. Code that relied on
`GetLanguage()` always returning None, or on `SetLanguage()` being a safe no-op,
will encounter changed behaviour. This is not a regression -- it is the fix --
but it is a detectable behaviour change.

**Test impact (MUST be tracked):**
`tests/operations/test_lexicon_brackets_live.py:409-424`
(`test_setlanguage_persists_to_the_lcm`) is currently marked `xfail(strict=True)`
because `SetLanguage` wrote to nonexistent `LanguageRA`. After R6:
- The xfail reason is obsolete; the method now works.
- The test body checks `hasattr(fresh, "LanguageRA")` -- that assertion is on the
  wrong field. It must be rewritten to verify `LanguageRS` is populated.
- T2 must NOT simply remove the xfail marker without rewriting the test body.
  Stripping `@pytest.mark.xfail` while leaving the `LanguageRA` assertion will
  pass today (the raw factory has both fields in its live dir) but will test the
  wrong thing. Full test rewrite is required; assign to T6 (test update wave).

**R5 -- No public API break.**
Setter-order constraint on `IConstChartMovedTextMarker` is an implementation
invariant. `GetSyncableProperties` / `ApplySyncableProperties` signatures are
unchanged. No callers need updating.

---

## 2. Sync Payload Key Changes

The following table covers all rulings that alter the dict shape emitted by
`GetSyncableProperties` or consumed by `ApplySyncableProperties`.

| Ruling | Operations class | Old key | New key | Change type |
|--------|------------------|---------|---------|-------------|
| R1 | `EtymologyOperations` | `"LanguageRA"` (str GUID or None) | `"language_rs"` (list\[str GUID\]) | Rename + type change |
| R2 | `EtymologyOperations` | `"LanguageNotesRA"` (always None) | *(removed)* | Removal of dead key |
| R3 | `LexReferenceOperations` | `"ReferenceTypeRA"` (str GUID or None) | `"owner_guid"` (str GUID) + new `"targets_rs"` (list\[str GUID\]) | Rename + addition |
| R4 | `TextOperations` | `"MediaFilesRC"` (always absent; hasattr no-op) | `"media_uris"` (list\[dict\]) | Rename + shape change |
| R7 | `LexSenseOperations` | `"DoNotShowMainEntryInRC"` (always `frozenset()`) | *(removed)* | Removal of dead key |
| R8 | `TextOperations` | *(absent)* | `"Name"` (MultiString dict) | Additive only |

### Payload key detail notes

**R1 `"language_rs"`:**
Shape change is significant. Old key was atomic (`str` or `None`);
new key is a list (`[]` when empty). Any code comparing or constructing
Etymology sync dicts must be updated. The `ApplySyncableProperties` handler
for `"LanguageRA"` in `_ra_fields` must be replaced with a dedicated list
handler for `"language_rs"`.

**R2 `"LanguageNotesRA"` removal:**
The key was always `None` due to a nonexistent field; it carried no information.
Any code that branched on `props.get("LanguageNotesRA")` would only ever see
`None`. Removal is safe. The `"Source"` key (backed by `LanguageNotes`
IMultiString) continues unchanged as the correct representation.

**R3 `"ReferenceTypeRA"` -> `"owner_guid"` + `"targets_rs"`:**
The old key was always `None` (hasattr guard on nonexistent `ReferenceTypeRA`).
Adding `"targets_rs"` is a net capability gain -- sync payloads now carry the
full ordered target list. The re-parenting behaviour change (different
`owner_guid` in incoming payload triggers delete+create) is new semantics with
no prior behaviour to preserve.

**R4 `"MediaFilesRC"` -> `"media_uris"`:**
Old key was always absent from the dict (hasattr no-op on nonexistent
`MediaFilesRC`). New key shape is richer:
`[{"uri": str, "file_guid": str|null}, ...]`. Strictly additive from a
data-presence standpoint (was never present), but the key name change means any
code checking `"MediaFilesRC" in props` will get `False` where it got `True`
before -- except it would have gotten `False` before too, because the key was
never written. Net effect: same behaviour for current callers; the new key is
only visible once the feature is actually working. R4 `needs_human` gap (no
live media project available) is carried forward per dispatcher decision.

**R7 `"DoNotShowMainEntryInRC"` removal from LexSenseOperations:**
The key was always `frozenset()` (hasattr guard on nonexistent field).
No semantic information was ever carried. Removal is safe.

**R8 `"Name"` addition:**
Purely additive. Existing consumers of the Text sync dict will not break;
they will simply start seeing a `"Name"` key they previously ignored. Sync
comparisons will now include the text name/title, which is the intended fix.

---

## 3. Scope Boundary: DoNotShowMainEntryInRC in LexEntryOperations

**CRITICAL SCOPING CONSTRAINT FOR T2:**

R7 is scoped to `LexSenseOperations` (lines 672-678, 712, 756). T0 confirmed
`DoNotShowMainEntryInRC` is absent on `ILexSense`. It did NOT test `ILexEntry`.

`LexEntryOperations.py` contains multiple references to `DoNotShowMainEntryInRC`
on entry objects:
- `line 421-422`: `Duplicate` copies `source_entry.DoNotShowMainEntryInRC`
- `lines 578-585`: `GetSyncableProperties` includes `DoNotShowMainEntryInRC`
- `line 631`: `_rc_fields` tuple
- `lines 2382, 2409, 2411, 2435, 2437`: dedicated publication-exclusion methods

These are on `ILexEntry`, not `ILexSense`. T0 did not reflect `ILexEntry` for
this field. T2 must NOT remove or alter these entry-level references based on R7.
If `ILexEntry.DoNotShowMainEntryInRC` is also absent from the LCM, that requires
a separate T0 reflection pass and a new ruling in a follow-on issue.

---

## 4. Required Migration-Guide Entries (for lex-doc T7)

Exact bullets lex-doc will need in `docs/MIGRATION_GUIDE.md`:

---

### Breaking Change: EtymologyOperations -- GetLanguage / SetLanguage deprecated (R6)

- `project.Etymology.GetLanguage(etym)` is deprecated. It now emits a
  `[WARN]` logger message and returns `project.Etymology.GetLanguages(etym)[0]`
  or `None`. Use `GetLanguages()` for the full ordered list.
- `project.Etymology.SetLanguage(etym, lang)` is deprecated. It now emits a
  `[WARN]` logger message and calls `SetLanguages([lang])`, replacing any
  existing sequence with a single-element list. Use `SetLanguages()` to set
  multiple languages.
- **NOTE: Prior to this fix, both methods were silently non-functional**
  (`LanguageRA` does not exist on the LCM). Any code that relied on
  `GetLanguage()` always returning `None`, or on `SetLanguage()` being a
  safe no-op, should be reviewed. The methods now operate correctly through
  `LanguageRS`.
- New methods: `GetLanguages(etym)` -> `list[ICmPossibility]` (ordered),
  `SetLanguages(etym, langs)` -> replaces entire `LanguageRS` sequence.

---

### Breaking Change: Sync payload key renames (R1, R3, R4) -- #325

Code that directly inspects dicts from `GetSyncableProperties` or constructs
dicts for `ApplySyncableProperties` must be updated:

- **EtymologyOperations** (R1): Key `"LanguageRA"` replaced by `"language_rs"`.
  Old value: `str` GUID or `None`. New value: `list[str]` of GUID strings (empty
  list if no languages set). Update any equality checks or dict constructors
  targeting `"LanguageRA"`.

- **EtymologyOperations** (R2): Key `"LanguageNotesRA"` removed. It was always
  `None`; remove any code that referenced it.

- **LexReferenceOperations** (R3): Key `"ReferenceTypeRA"` replaced by
  `"owner_guid"` (str GUID of the owning `ILexRefType`). New key `"targets_rs"`
  added (list of GUID strings, ordered). Update dict references. Note: providing
  a different `owner_guid` in an `ApplySyncableProperties` call now triggers a
  delete-and-recreate operation, not an in-place property update.

- **TextOperations** (R4): Key `"MediaFilesRC"` replaced by `"media_uris"`
  (list of dicts: `{"uri": str, "file_guid": str|null}`). Update dict
  references. The old key was never populated (hasattr no-op); this is a
  functional replacement.

---

### Change: Sync payload key removal (R7) -- #325

- **LexSenseOperations**: Key `"DoNotShowMainEntryInRC"` removed from
  `GetSyncableProperties` output. It was always `frozenset()` (absent LCM
  field). Remove any code that branched on this key in sense sync dicts.

---

### Change: Sync payload addition (R8) -- #325

- **TextOperations**: Key `"Name"` added to `GetSyncableProperties` output
  (MultiString dict, same structure as `"Description"`). Sync comparisons and
  merges for texts now include the text title. Purely additive; no existing
  payload key is removed or renamed.

---

## 5. Verdict

**APPROVE wave 1 to proceed**, with the following binding constraints for T2
implementers:

1. **T2 -- R7 scope:** Do NOT alter `LexEntryOperations` references to
   `DoNotShowMainEntryInRC`. R7 is `LexSenseOperations` only.

2. **T2d -- R5 gap declaration:** The PR description must explicitly state
   which path was taken (option a: adopt #290 model + `# VERIFY in T3`
   comment, or option b: block on follow-on T0). No third option (claim done
   without either) is compliant.

3. **T2 / T6 -- R6 test rewrite:** `test_setlanguage_persists_to_the_lcm` in
   `test_lexicon_brackets_live.py` must be fully rewritten (not just
   xfail-stripped). The test body asserts on `LanguageRA`, which is wrong after
   R6. Assign rewrite to T6; T2 must leave the xfail marker in place until T6
   completes.

4. **T2c -- R4 media gap:** `GetMediaFiles`/`AddMediaFile` discrepancy
   (`MediaFilesOC` vs `MediaURIsOC`) stays open. T2c implements `media_uris`
   key only; it does not fix `GetMediaFiles`/`AddMediaFile`. Document the
   unverified gap in T2c's evidence file.

5. **No new `needs_human` blockers** beyond the existing R4 live-media gap.
   All other rulings are grounded in T0 live evidence (run_mode=live, 6/6 passed)
   and carry no unresolved questions that would block T2.

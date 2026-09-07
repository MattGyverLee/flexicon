# Live verification (independent, cycle 3) -- T2 (`_ResolveFeatureStrucOwner`) + T3 (`_GetFeatureStruc`, `_ResolveFsByGuid`)

**Project:** `target_sandbox` (write-path), `sena3_sandbox` + real "Ngoreme FLEx"
(read-only) for Part 4. Real Target/Sena3 never opened write-enabled.
**Baseline:** commit `1790fcc0`.
**Date:** 2026-09-07

## Part 1 -- measured baseline (stash push source files only, test file left in place)

`git stash push -- flexicon/code/BaseOperations.py flexicon/code/Shared/lcm_constants.py`,
confirmed via `git status` that only those two files reverted.

BEFORE (baseline):
- Offline (`tests -m "not requires_live_project"`, excluding new file for the
  count): **1277 passed**.
- Offline including the new test file: collection **ERROR**
  (`ImportError: cannot import name 'FEATURE_STRUC_OWNER_TABLE'`) -- all 13
  offline tests in the new file fail-to-collect, as expected (helpers do not
  exist yet). This IS the "new test fails at baseline" proof.
- Live, new file alone (`FLEXLIBS_REQUIRE_LIVE=1`): same collection ERROR.
- Live, zero-delta set (`test_owner_cast_pattern.py::TestFeatureStructOwnerCastT1`,
  `test_natural_class_feature_sync.py`, `test_issue251_252_256_feature_struct_probe.py`):
  **9 passed**, `run_mode: live`.
- Known pre-existing failure
  `test_natural_classes.py::TestNaturalClassSync::test_apply_raises_on_type_mismatch_segments_target`:
  **FAILED** (re-checked separately at baseline).

`git stash pop`, confirmed via `git status` full T2/T3 diff restored.

AFTER:
- Offline: **1290 passed** (`tests -m "not requires_live_project"`).
- Live, new file: **16 passed**, 13 deselected, `run_mode: live`.
- Live, zero-delta set: **9 passed** -- identical test IDs/outcomes to BEFORE.
- Known pre-existing failure: **FAILED** -- identical to BEFORE.

Both BEFORE and AFTER live runs confirmed `tests/live_status.json`
`"run_mode": "live"`.

**Mid-audit incident (disclosed):** during Part 3's mutation test, a
`git checkout --` was run against the wrong target and briefly discarded the
uncommitted T2/T3 `BaseOperations.py` working-tree changes. Recovered
byte-exact via a dangling blob left over from the earlier `stash push/pop`
(`git cat-file -p b90738622100c945c94f607bfba0002db6b928bb`, hash verified
against `git hash-object` post-restore). Offline (1290) and live (16) suites
re-confirmed green after recovery. Separately, this agent's own
case-variant filename for this evidence file briefly overwrote the
programmer's `live-t2-t3.md` on this case-insensitive filesystem; that file
was restored verbatim from the text captured earlier in this same
verification session, and this report was renamed to a non-colliding name.

## Part 2 -- zero-delta audit

`git diff --stat` on `NaturalClassOperations.py`, `PhonemeOperations.py`,
`PhonFeatureOperations.py`, `InflectionFeatureOperations.py`,
`MSAOperations.py`, `POSOperations.py`, `AllomorphOperations.py`: all
empty -- byte-unchanged. `NaturalClassOperations.__ResolveByGuid` (line
1403) and `PhonemeOperations.__ResolveByGuid` (line 1525) both present
verbatim; the `test_apply_features_raises_on_unresolved_feature_guid`
source-pin (the `src.index("feat_obj = self.__ResolveByGuid")` assertion)
passes.

`grep -rl` for the property names and `FEATURE_STRUC_OWNER_TABLE` repo-wide
(excluding `build/lib`): only `BaseOperations.py` (consumer), `lcm_casting.py`
(a comment mentioning the property names, no table), `Shared/lcm_constants.py`
(the one definition), and two test files. Exactly ONE copy of the table.

Table rows compared line-by-line against spec.md section 4 C1 (lines
284-293): identical, 8 keys / 10 rows, same slots, same owning properties,
same props keys. `PosFeatures` and `FsComplexFeature` are absent from both
the code table and the spec table (confirmed by
`test_excluded_classnames_absent_from_table`, live-passing).

## Part 3 -- anti-trap audit

Every live T2 test builds its object via `sandbox.Object(hvo)` (a bare
`ICmObject`), never a factory-fresh reference -- confirmed by direct reading.
Mutation test performed: temporarily replaced
`concrete_owner = interface_type(unwrapped)` with
`concrete_owner = unwrapped` (cast deleted) and re-ran the live suite:
12/16 tests failed (all 10 parametrized resolve cases plus the two T3
struct-round-trip tests), 4 passed (the raise-branch and GUID-resolution
tests that do not depend on a successful cast). This proves the tests
exercise the real cast, not a tautology. Restored, hash-verified identical
(`git hash-object` matching `b90738622100c945c94f607bfba0002db6b928bb`).

T3's nested-struct test confirmed built with raw `IFsFeatStrucFactory` /
`IFsComplexValueFactory` / `IFsClosedValueFactory` calls only (no
`MakeFeatStruc`), ownership-first at every level; post-state re-queried via a
fresh `project.Object(stem.Hvo)` fetch, and asserted against write-time GUIDs
recorded from the real definitions, not against an input dict (there is no
input dict here -- the assertions compare against live-object GUIDs captured
before serialization).

Empty-but-present case: `_GetFeatureStruc` on a real attached, zero-spec
`IFsFeatStruc` (`InflFeatsOA`) yields `{"TypeGuid": None, "specs": {}}` --
confirmed NOT `None`.

Per-level `TypeGuid`: outer `TypeRA` never set, so `result["TypeGuid"] is
None`; inner `TypeRA` set to a real `IFsFeatStrucType`, so the nested dict
`"TypeGuid"` equals that type GUID. Both round-trip correctly in the same
test.

## Part 4 -- open measurement: do NC/Phoneme feature structures ever nest?

Sena 3 (`sena3_sandbox`) is uninformative for this question: 18
`PhNCFeatures`-or-`PhNCSegments` NaturalClass objects, 0 are `PhNCFeatures`
(all segment-based); 44 `PhPhoneme` objects, 0 have a non-null `FeaturesOA`.

Switched to "Ngoreme FLEx" read-only (the same populated project cycle-1
used for its 799/820 MSA measurement, and the most populated project
available for phonology data), per the task's own "or a read-only open"
allowance:

```
PhNCFeatures: 41/48 NC objects are feature-based, all 41 have non-null FeaturesOA
  spec ClassNames across those 41 structs: complex=0, closed=76
PhPhoneme: 41/41 phonemes have non-null FeaturesOA
  spec ClassNames across those 41 structs: complex=0, closed=779
```

Raw counts: NC complex=0/closed=76 (0/76 nested); Phoneme complex=0/closed=779
(0/779 nested). Across 855 total specs examined, zero `IFsComplexValue`. This
CONFIRMS the code comments at `NaturalClassOperations.py:1145-1148` and
`PhonemeOperations.py:1358-1362` -- in live data, NC/Phoneme feature specs are
100% closed-value, never complex/nested. This is the opposite finding from
MSA (99.7% nested) and directly lowers T9b's priority: the legacy flat-list
capture format is measured, not just asserted, to be non-lossy for NC/Phoneme
today.

(Scratch test file used for this measurement was written to
`tests/operations/`, run, and then deleted -- not part of the deliverable;
this is a verification-agent read-only probe, not a programmer artifact.)

## Part 5 -- archivist spec edit audit

`git diff specs/feature-structure-sync-gap/spec.md`: all changes are markdown
prose/checklist edits (D3 correction, new D3a, new C4a/C4b, section-5 T1/T11
updates). No other file touched by this diff. The C1 table itself (section 4)
is untouched by the diff and still matches the code table exactly (Part 2).

Minor observation (not a fail): section 5's checklist still shows T2 and T3
as unchecked, even though the programmer report claims both complete. This
predates or is concurrent with the programmer commit and is a reconciliation
item for the next cycle, not a docs-only violation.

## Result

PASS -- every claim in the programmer report and evidence file was
independently reproduced against a live LCM, with a genuinely measured (not
asserted) baseline, a real zero-delta audit, and a mutation test proving the
new tests exercise live dead code rather than passing tautologically.

# Cycle 15 -- LEG 2b (P2 live-half COMPLETION): LEAD PREDICTIONS

**Committed BEFORE any cycle-15 run, per `prediction_commitment_rule`
(BINDING from cycle 13, from cycle12-lead-ruling-2).**

Author: /lex-lead, cycle 15 dispatch. Date: 2026-09-07.
Parent commit at authoring time: `7786ba9`.
Subjects under test: `4e9d152` (production) + `4b746a0` (tests), pre-T7
comparison point `1d88aa4`.

## Why this leg exists

Cycle 14's gate returned PASS and its LEG 2 measured ZERO flips across 90
collected live items at both commits. Neither of G3's committed falsifiers
fired. But the lead's cycle-14 adjudication established, first-hand, that
LEG 2's enumeration was INCOMPLETE, and incomplete on exactly the sites the
residual is about:

- The node-id list actually passed to pytest (evidence/live-cycle14-gate.md
  lines 154-234) spans **15** distinct files, not the 16 the report claims
  in three places.
- The claim "STRICT SUPERSET of the 12-file main-session floor list" is
  FALSE. `tests/operations/test_grammar_brackets_live.py` is a
  POS-touching live file that the gate never enumerated and never mentions.
- That file's `TestPOSBrackets` (4 live tests, `target_sandbox` fixture, so
  sandbox-safe) calls `pos_ops.Create / SetName / GetName / SetAbbreviation
  / GetAbbreviation / Delete / GetAll`. Mapping the 16 `__ResolveObject`
  call sites to their enclosing methods gives:
  `Delete:273, GetName:401, SetName:439, GetAbbreviation:474,
  SetAbbreviation:511, GetSubcategories:555, AddSubcategory:617,
  RemoveSubcategory:673/674, GetCatalogSourceId:711,
  GetInflectionClasses:751, GetAffixSlots:792, GetEntryCount:841,
  Duplicate:913, GetSyncableProperties:1216, ApplySyncableProperties:1305`.
  So `TestPOSBrackets` exercises **five of the fourteen pre-existing call
  sites**, and it is the ONLY live file that exercises the POS **write**
  path. It was run at NEITHER commit.
- Root cause of the miss: the gate's regex (`\.POS\.` / `project.POS` /
  `POSOperations` / `IPartOfSpeech(`) does not match the local-alias
  pattern `pos_ops = target_sandbox.POS` followed by `pos_ops.SetName(...)`.
  A lead scan for that alias pattern across all live test files finds
  exactly ONE genuinely missed file, so the gap is bounded and singular.

---

## [PREDICTION] H1 -- `TestPOSBrackets` runs GREEN at BOTH commits, zero flips (BLOCKING)

`tests/operations/test_grammar_brackets_live.py::TestPOSBrackets` (4 live
tests) run with `FLEXLIBS_REQUIRE_LIVE=1` at `1d88aa4` (disposable
worktree) and at HEAD, same shell, both `run_mode: live`: **4 passed at
both, identical pass pattern, zero flips in either direction.**

Confidence: high. The cast is strictly widening -- it turns a bare
`ICmObject` into `IPartOfSpeech`, adding attributes, removing none. These
four tests also pass an already-typed object (`created`, from
`pos_ops.Create`) rather than an HVO, so most of them likely never enter
`__ResolveObject`'s HVO branch at all.

**Falsifier, and it is a P0 if it fires:** a GREEN -> RED flip. That is
G3a's never-exercised falsifier finally getting an honest test on the
write path -- it would mean a pre-existing `POSOperations` write method
duck-types on the ABSENCE of an `IPartOfSpeech` attribute, and T7 shipped
a real regression at a site it never tested. Checkpoint 4 does not close;
report it FIRST and in full.

**Second falsifier (non-blocking, still record it):** RED at BOTH commits.
Then the file has a pre-existing failure unrelated to T7 -- note it, do not
attribute it to T7, and say so explicitly.

## [PREDICTION] H2 -- the alias-pattern miss is SINGULAR

Re-running the lead's alias scan independently (find every live-marked test
file containing `= <something>.POS`, diff against the gate's 15-file set)
finds exactly TWO files outside the set:
`test_grammar_brackets_live.py` (the genuine miss) and
`test_issue252_pos_feature_sync.py` (the new T7 file, excluded BY DESIGN
and unrunnable at `1d88aa4`).

**Falsifier:** a third file. Then the gap is not singular, LEG 2b must widen
to cover it too, and the enumeration method itself needs re-deriving rather
than patching.

## [PREDICTION] H3 -- the true item-level denominator is stated, not the file-level one

The 15 files the gate DID enumerate contain **145** `requires_live_project`
items by `--collect-only` (lead-measured). The gate ran **81 node-ids /
90 collected**. PREDICTED: this reproduces -- so even inside its own file
set the gate exercised ~62% of available live items, and the honest
statement of LEG 2's coverage is "90 of 145 live items in 15 files, plus
LEG 2b's 4, with the remainder named and deliberately not run".

**Falsifier:** the collect-only count differs materially from 145. Then the
lead's own denominator is wrong and must be corrected in STATUS.md.

**Explicitly NOT required:** running the other ~55 items. Six of the 15
files open a REAL, in-place, named FieldWorks project rather than a sandbox
copy (the gate flagged this). Doubling in-place exposure to chase the last
38% is a worse trade than naming the residual honestly. State what was not
run and why; do not run it.

## [PREDICTION] H4 -- the CHANGELOG amendment is additive only

The `CompareTo` disclosure added to `CHANGELOG.md` touches ONLY the
existing `4e9d152`/#252 entry, adds no new version heading, and changes no
existing line's meaning.

**Falsifier:** the amendment restructures the entry or edits unrelated
lines. Then it needs a second read before it is committed.

---

## Standing rules in force for cycle 15

- Rule 1 (locks) RETIRED. Rule 2 (one live-pytest token) BINDS -- only
  lex-verification runs live this cycle; lex-doc runs nothing.
- AMENDED git procedure. Disposable worktrees mandatory for the `1d88aa4`
  side.
- Never stage the five known foreign noise items.
- NO GitHub action of any kind. #252 closure needs the user's own
  authorisation, exactly as #251's did.

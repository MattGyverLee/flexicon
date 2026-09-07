# SPEC -- name-field-whitespace-identity

**Repo:** flexicon, branch `main`
**Issues:** flexicon#242 (parent whitespace campaign), sub-items Q-242A and
Q-242B of `specs/tier1-silent-data-loss/QUEUE.md`
**Campaign:** `tier1-silent-data-loss`, spun-out sub-item **2a** (between
queue item 2, `242-paragraph-whitespace`, and queue item 3,
`feature-structure-sync-gap`)

**Status:** CHECKPOINT 1 (spec + live probe) DONE, 2026-09-07. No behaviour
change under `flexicon/code/` has been authorised by THIS feature yet --
this feature's own crew made zero Edit/Write calls under `flexicon/`.
(`git status` shows unrelated modifications to `flexicon/code/BaseOperations.py`,
`flexicon/code/Grammar/NaturalClassOperations.py`, and
`flexicon/code/Grammar/PhonemeOperations.py` -- these belong to the second,
concurrent crew described in `CONCURRENCY.md` and are NOT this feature's
work; do not attribute them here, do not stage them, do not revert them.)
Contract items C1-C8 below are FROZEN, transcribed substantially verbatim
from the ruling that authorised this feature. `tasks.md` derives the
implementation tasks from them.

**Read first, and read in this order:**
- `specs/name-field-whitespace-identity/CONCURRENCY.md` -- binding on every
  task in this feature; a second, owner-confirmed crew is committing in
  this same clone right now.
- `specs/tier1-silent-data-loss/QUEUE.md` (Q-242A, Q-242B, Q-242C)
- `specs/242-paragraph-whitespace/spec.md` (C1, C5, C6, C7, C10, C11
  especially -- this feature corrects and extends #242's C10)
- `specs/name-field-whitespace-identity/reviews/cycle1-programmer.md` and
  `evidence/live-probe-cycle1.md` -- the measured results folded in below
- `specs/name-field-whitespace-identity/reviews/cycle1-domain.md` -- the
  deciding ruling on the identity question

**Numbering convention:** this feature's own contract items are C1..Cn,
local to this spec. Any reference to the #242 feature's contract is written
as **"#242 C10"** (with the issue number), never bare "C10" -- the two specs
cite each other constantly and the numbering would otherwise collide.

---

## 0. Authority and provenance (read before C1-C8)

The ruling authority on this feature's central question -- whether dedup
comparisons should become whitespace-insensitive -- **changed mid-cycle**,
and that change is recorded here explicitly rather than silently folded
into a single verdict:

1. `/lex-lead` ruled C1-C8 below (the initial pass, covering the mechanism
   findings C1/C2, the identity ruling C3, the fix shape C4, the scope C5,
   the Q-242A/Q-242B bundling C6, and Q-242B's own fix shape and boundary
   C7, plus the anti-regression pin C8).
2. **The project owner then directed:** "Let's do what is best for the
   user, /lex-domain can decide," which placed the identity question (C3)
   under `/lex-domain`'s authority -- an owner override of `/lex-lead`'s
   standing decision-making role for this one question.
3. **`/lex-domain` independently re-tested C3 and ACCEPTED `/lex-lead`'s
   option (i)** -- whitespace-insensitive comparison, raw-byte persistence
   -- on its own, independently-grounded FLEx-domain reasoning (see
   `reviews/cycle1-domain.md`, transcribed in full at C3 below).

**Consequence, stated so a future reader cannot miss it:** C3 stands, but
it now stands on **`/lex-domain`'s verdict and the owner's "best for the
user" standard**, not solely on `/lex-lead`'s original reasoning. This is
not a rubber stamp -- `/lex-domain` was given the authority to overturn
`/lex-lead` and instead re-derived the same answer from independent
grounds (the uniqueness guard is a flexicon invention, not a FLEx/LCM
invariant; see C3 below), which is materially different from simply
inheriting the prior ruling.

---

## 1. Problem statement

`specs/tier1-silent-data-loss/QUEUE.md`'s cycle-2 sibling sweep
(`specs/242-paragraph-whitespace/spec.md` C7/C10) found 8 name-field
writer sites sharing #242's bug shape (strip -> validate -> persist the
stripped copy), routed out of `242-paragraph-whitespace` as two separate,
more carefully triaged asks:

- **Q-242A** -- the 8 sibling sites themselves, blocked on a name-field
  identity/dedup ruling (this feature's C3).
- **Q-242B** -- a distinct, MORE SEVERE defect at `CheckOperations.py`:
  a non-str payload or a whitespace-only string is silently coerced to
  `""` and persisted with **no exception at all** -- total payload loss,
  not merely lost padding.

Both are now **AUTHORISED BY THE OWNER, 2026-09-07**, and this feature is
where they are implemented together (C6 explains why together, not as two
independently-scheduled features).

---

## 2. Contract items (FROZEN)

Transcribed substantially verbatim from the ruling that authorised this
feature. These may not be overturned, softened, or re-derived by any task
in this feature; a contradiction found during implementation is reported
as a finding and escalated, not silently resolved.

### C1 -- The dedup comparisons strip the NEEDLE only, never the HAYSTACK

`TextOperations.Exists` (strip `:458`, needle key `:461`, haystack key
`:464`); `AnthropologyOperations.Find` (`:558`/`:562`/`:565`, reached via
`Exists` `:507-510`); `CheckOperations.FindCheckType` (`:341`/`:344`/`:350`).
`normalize_match_key` (`Shared/string_utils.py:50-83`) =
`normalize_text` + NFD + optional casefold, and does **NOT** strip. Today
the haystack is stripped BY CONSTRUCTION, because the only library path
that writes these names strips first. **THE WRITER'S STRIP IS
LOAD-BEARING FOR DEDUP COHERENCE, NOT INCIDENTAL TO IT.**

**Live confirmation (cycle 1, `evidence/live-probe-cycle1.md`):** PN2
(`TextOperations`), PN3 (`AnthropologyOperations`), PN4
(`CheckOperations`) all measured exactly as predicted -- a layer-B-written
name carrying a trailing space is invisible to `Exists`/`Find`/
`FindCheckType` for BOTH an unpadded and a padded needle, because the
needle is always stripped but the haystack (the raw stored name) never
is. **No refutation** -- all three binding predictions MATCHED.

### C2 -- A PERSIST-ONLY FIX PRODUCES DUPLICATES, NOT REJECTIONS

This explicitly **CORRECTS #242 C10**, which said the risk of fixing
persist-only was "Genesis " coexisting with "Genesis". The real
behaviour, live-confirmed: `Create("Genesis ")` persists "Genesis "; a
second identical call strips its needle to "Genesis", fails to match
the stored "Genesis ", and creates a **SECOND record** -- unbounded
duplicates of a name byte-identical to itself. Neither candidate (i) nor
(ii) from #242's own framing, but a **third semantics reachable only by
omission**.

**Live confirmation (PN8, `evidence/live-probe-cycle1.md`):** layer-B
store "TEST_NF_Dup " (trailing space), then call the public
`Texts.Create("TEST_NF_Dup ")` -> **SUCCEEDS, no `FP_ParameterError`**;
exactly two `IText` objects end up matching the same displayed name. The
binding claim MATCHED. **One flagged, non-binding sub-detail, reported
plainly and not smoothed over:** the second (public-API-created) record's
stored name measured as "TEST_NF_Dup" (no trailing space), NOT
byte-identical to the first -- because `Create()`'s CURRENT (pre-fix)
persist writes its own already-stripped local `name`, not the caller's
original argument (`TextOperations.py:152`, reused at `:170-171`). This
does not weaken C2's binding claim (persist-only produces a duplicate,
not a rejection); it is a measurement artifact of testing the mechanism
against code that has not yet had C4's persist fix applied. Once C4 lands,
both records in this scenario would be persisted from the caller's
original, unstripped argument and would be byte-identical, matching C2's
illustrative wording exactly.

This correction to **#242 C10** is recorded openly, AS a correction; #242
C10 is not silently superseded.

### C3 -- RULING: whitespace-insensitive dedup, ACCEPTED (lex-lead, ACCEPTED by lex-domain under owner override)

Whitespace-insensitive dedup is **ACCEPTED**, made **EXPLICIT and
SYMMETRIC**: both sides of every comparison are stripped at the
comparison site, and the persist takes the caller's original bytes.
Whitespace-**SENSITIVE** dedup is **REJECTED** -- the owner authorised
fixing a silent-data-loss bug, not redefining name identity; it would
change the published semantics of three lookup predicates and create a
FLEx footgun where two list items differ by an invisible character.
**Per-family rules are REJECTED as policy**: `DiscourseOperations` has no
comparison at all, so C3's comparison half has nothing to act on there.

**lex-domain's independent grounds, which strengthen this ruling**
(transcribed from `reviews/cycle1-domain.md` in full):

- **Grounding checked in source:** `TextOperations.py:118,134-135`
  documents `Create`'s uniqueness ("must be unique and non-empty" /
  raises `FP_ParameterError` if a text with this name already exists) as
  a **library-invented policy** -- `IText.Name` carries no such constraint
  in the LCM model itself, and FLEx's own Texts & Words organizer
  enforces **zero** title uniqueness (duplicate "Untitled Text",
  re-imported duplicates from revision workflows, and repeated
  Scripture-portion titles across drafts are all routine, unremarked-on
  FLEx states). `AnthropologyOperations.py:252,265,269` documents the same
  invented-uniqueness shape for OCM/`CmAnthroItem` names.
  `CheckOperations.py`'s "check type" is this library's own concept
  layered on `ICmPossibilityList`, not a native FLEx-UI list a user
  browses. **So C3 decides what OUR guard means and overrides no native
  FLEx semantic.**
- **Q1** (is the guard itself FLEx-faithful?): FLEx name-entry boxes for
  these fields are plain single-line `ITsString` editors; nothing in the
  LCM model or FLEx's UI code trims on commit, and #242 C5's own finding
  (`AppendSentence` manufacturing ". " and storing it verbatim)
  confirms FLEx's general philosophy is "store what was typed," not
  silent reformatting. For text titles specifically, FLEx enforces **no**
  uniqueness at all -- two items differing only by a trailing space
  absolutely can, and functionally already do, coexist in real FLEx
  projects. This argues candidate (ii) (no dedup change) is more
  FLEx-faithful in the narrow sense of reproducing total permissiveness
  -- but it also means the uniqueness guard being debated is not itself a
  FLEx invariant to preserve either way; it is flexicon's own value-add.
- **Q2** (is whitespace ever meaningful in these names?): text titles --
  yes, sort-order padding hacks and import artifacts (Paratext \h,
  Word/PDF copy-paste, Toolbox migration) genuinely introduce
  meaningful-to-the-user padding. OCM/Anthropology names -- rare, the
  standard catalog carries no such convention, though user-added
  subitems could inherit copy-paste whitespace. Check-type names --
  essentially never, these are ad hoc user labels for a library feature
  with no whitespace convention at all. The "meaningful whitespace"
  argument is real but strictly weaker and rarer for names than for
  paragraph content.
- **Q3** (does #242 C5's structural-whitespace argument extend to names?):
  #242 C10's content-vs-name distinction is sound at the level it was
  making it -- nothing in the LCM name-field type or in any name-writer
  manufactures whitespace as structure the way `AppendSentence`
  manufactures ". ". The closest analog, user sort-order hacks, is
  user-imposed convention, not FLEx/LCM-generated structure; it does not
  rise to #242 C5's level and does not overturn #242 C10. It does mean
  #242 C10 slightly **understates** why raw-byte persistence still
  matters for names (sort hacks, import fidelity) -- but that is an
  argument for the **persist** half, not the dedup half; persist-vs-strip
  and identity-for-comparison are properly separable, which is exactly
  what this ruling does.
- **Q4** (which serves the user better?): (i) serves the user better. A
  guard the user relies on ("Exists returned False, so Create is safe")
  that can be silently defeated by one invisible character is a
  false-confidence footgun, **worse than no guard at all** --
  precisely the population most exposed to it (import/round-trip users)
  is the population most likely to already have stray whitespace. (i)
  surfaces the collision as an actionable `FP_ParameterError` naming the
  existing record; (ii) produces two rows in a FLEx list/tree that render
  pixel-identical, with no FLEx affordance to distinguish them.
- **Q5 -- ACCEPTED.** Persist the caller's raw bytes; strip both sides at
  every uniqueness comparison. This does not redefine what a name is --
  the model still stores exactly what the caller typed. It defines what
  flexicon's own, library-invented uniqueness guard treats as a
  collision, and it should treat whitespace as insignificant for that
  purpose because the guard exists to protect users from accidental
  duplication, and an invisible-character bypass defeats that entire
  purpose while serving no compensating value -- FLEx itself enforces
  nothing here, so there is no native semantic being overridden.

### C4 -- HOW, and the shared-code fence

Do **NOT** add `.strip()` to `normalize_match_key` (~80 call sites; the
widening #242 C11 exists specifically to prevent this). Do **NOT** add a
new shared helper either -- six local call sites do not justify a new name
in `Shared/string_utils.py` that invites reuse everywhere. **Strip INLINE
at the six comparison points:**

```
target = normalize_match_key(name, casefold=...).strip()
... normalize_match_key(candidate, casefold=...).strip() == target
```

`normalize_match_key` returns `""` for `None`, so the haystack side is
safe. `flexicon/code/Shared/string_utils.py` and
`flexicon/code/BaseOperations.py` are **NOT edited by this feature** --
and per `CONCURRENCY.md`, `BaseOperations.py` is additionally the other
crew's live working file, so that fence is now absolute. **If an
implementer concludes either must change: STOP, needs_human.**

### C5 -- SCOPE

The three comparison methods (`TextOperations.Exists`,
`AnthropologyOperations.Find`, `CheckOperations.FindCheckType`) are **IN
SCOPE** and this is **NOT scope creep** -- they are the other half of the
same edit, and fixing the persist without them **IS** the C2 duplicate
explosion. **Total touched files: 4** --
`flexicon/code/System/CheckOperations.py`,
`flexicon/code/TextsWords/TextOperations.py`,
`flexicon/code/TextsWords/DiscourseOperations.py`,
`flexicon/code/Notebook/AnthropologyOperations.py`.

**Observation, NOT a task:** `AnthropologyOperations.CreateSubitem` has
no dedup check at all, unlike `Create` -- **do not add one**.

### C6 -- Q-242B TRAVELS WITH Q-242A

One feature, separate tasks, separate severity labels, separate CHANGELOG
entries, separate live evidence. They are the same two expressions
(`CheckOperations.py:196` is simultaneously a Q-242A site and the
Q-242B site), so two features editing one expression in sequence is pure
overhead. Separate FILING already served its purpose -- it was ruled on
its own merits and reached the owner as its own item; that purpose is met
by separate tasks, not separate directories.

### C7 -- Q-242B FIX SHAPE, AND THE HARD Q-242C BOUNDARY

Q-242B does **NOT** require answering Q-242C. Replace
`name = name.strip() if isinstance(name, str) else ""` at
`CheckOperations.py:196`, `:341` and `:432` with a call to the
**ALREADY-SHIPPED** `BaseOperations._ValidateStringNotEmpty` (`:2491`) --
**CALLING** it, not editing it -- with **no reassignment of `name`**;
persist the original. That helper already opens with
`if not isinstance(text, str): raise TypeError(...)`, so this changes
zero shared code, decides no coercion policy, and conforms
`CheckOperations` to three sites already inside the authorised eight
(`TextOperations.Create:151`, both `DiscourseOperations` sites). It also
fixes a **SECOND silent path** not previously named:
`CreateCheckType("   ")` today strips to `""`, passes the None-only
`_ValidateParam`, and persists an empty name with no exception.

**Two details that must NOT be got wrong:**

(a) **KEEP** the existing leading `_ValidateParam(name, "name")` call at
each site. `_ValidateStringNotEmpty(None)` raises `TypeError` -- its
`if text is None` branch is unreachable dead code -- so dropping the
guard would silently change the `None` exception type from
`FP_NullParameterError`. **Record the dead branch as an OBSERVATION
ONLY** -- fixing it is shared code and out of scope.

(b) Do **NOT** harmonise the three `AttributeError` sites
(`TextOperations.SetName`, `AnthropologyOperations.Create` and
`CreateSubitem`). That is an exception-type change at sites with no data
loss, and it belongs to **Q-242C**.

**THE LINE:** we convert SILENCE into LOUDNESS (authorised, Tier-1); we
do not re-shape WHICH loud error an already-loud site raises (not
authorised).

**lex-domain's Q6, settling the whitespace-only case which C7 had left
implied:** a whitespace-only name raises `FP_ParameterError`, on **both**
the str and non-str branches, matching #242's four content writers.
"A name is a display label with no legitimate all-whitespace state in
any FLEx list/tree rendering -- unlike paragraph content, there is no
structural or transient-editing argument for an invisible name, only the
confusing blank-row UI state this campaign exists to eliminate. No
FLEx-specific reason favors leniency here."

**The three-way non-str split across the eight authorised sites,
live-confirmed by PN7** (`evidence/live-probe-cycle1.md`): 3 typed
`TypeError` (via `_ValidateStringNotEmpty`, e.g. `TextOperations.Create`,
`DiscourseOperations.CreateChart` -- both measured), 3 `AttributeError`
(bare `.strip()` after a None-only `_ValidateParam`, e.g.
`AnthropologyOperations.Create`, `TextOperations.SetName` -- both
measured), 2 silent empty-name persist (`CheckOperations`'s two
`name.strip()`-else-empty-string writer sites, this feature's own C7 fix
target). PN7's four measured cases MATCHED their predictions exactly:
a `TypeError` naming the required type for `TextOperations.Create` and
`DiscourseOperations.CreateChart`, and an `AttributeError` for having no
`strip` attribute for `AnthropologyOperations.Create` and
`TextOperations.SetName`.

### C8 -- THE ANTI-REGRESSION PIN every code task must produce, live

`Create(<name with trailing space>)` twice -> the second RAISES
"already exists", **AND** the stored value re-reads **BYTE-IDENTICAL**
from the LCM. Those two assertions together are the entire ruling. If
either fails, the fix is wrong.

**Family-specific note:** `DiscourseOperations` has no dedup check at all
(C3's per-family carve-out), so the "raises already exists" half of C8
does not apply there -- only the byte-identical persist half is
pin-worthy for that family. For the three families with a dedup check
(`TextOperations`, `AnthropologyOperations`, `CheckOperations`'s
`CreateCheckType`), both halves apply.

### C9 -- The CheckOperations live-verification workaround BOUNDARY (governs T4)

The ONLY test-harness workaround authorised to reach `CreateCheckType`'s
own name-handling logic is a **test-instance-only monkeypatch of
`_GetCheckList` ALONE**, returning a **real LCM `ICmPossibilityList`**
obtained from the live sandbox project -- the `_seed_valid_check_list()`
pattern already in `tests/operations/test_name_field_identity_probe.py`
from cycle 1.

Explicitly NOT authorised. Each one is STOP, `needs_human`:
- patching `_GetOrCreateCheckList`;
- patching `ServiceLocator`, `GetInstance`, or `GetService`;
- returning a Mock, stub, fake, or any non-LCM object in place of a real
  `ICmPossibilityList`;
- patching `CreateCheckType`, `FindCheckType`, or `SetName` themselves,
  or any part of the code under test;
- editing ANY line under `flexicon/` to make the test reachable -- this
  includes "just fixing" `CheckOperations.py:1198`'s `GetInstance` ->
  `GetService`, which is Q-CHK1 and is NOT authorised.

Rationale: a workaround that replaces the object under test, or that
reaches past `_GetCheckList` into the LCM plumbing, produces a run that
proves the harness works, not that the fix works. The single-seam rule
keeps `CreateCheckType`'s own body -- validation, persist, dedup --
entirely unmocked and genuinely exercised.

If the single authorised seam turns out to be insufficient to reach the
persist line, the correct outcome is `FAIL: unverified` plus a recorded
candidate row -- NOT a wider workaround. This is exactly what happened to
T1 at `DiscourseOperations.CreateChart` (see C10(a) and Q-DISC1).

### C10 -- Mandatory non-exercise disclosure, and the Q-242B severity correction

**(a) Every evidence file this feature writes from cycle 3 onward MUST
contain a section headed exactly `## WHAT WAS NOT EXERCISED`**, listing:
every pin half not independently exercised live; every code path confirmed
by inspection only; every monkeypatched seam and what it displaced; and one
line for each saying why. An evidence file without this section is
INCOMPLETE and its task is not done. If everything in the task's pin was
genuinely exercised, the section still appears, reading
`None -- every pin half was exercised live.`

This is retro-fitted, not just forward-looking. Two existing evidence files
must gain the section:
- `evidence/live-t1-discourse-fix.md` -- `CreateChart`'s persist half
  (T1-P1) is `FAIL: unverified`, blocked by two pre-existing, unrelated
  defects (Q-DISC1); confirmed by code inspection only.
- `evidence/live-t2-text-fix.md` -- T2-P1 confirmed by inspection plus
  indirect live evidence; T2-P2 confirmed by inspection plus PN7's
  unchanged `AttributeError`; T2-P6 not independently re-asserted.

**(b) Q-242B severity correction.** `specs/tier1-silent-data-loss/QUEUE.md`'s
Q-242B row describes the defect as reachable by a **non-`str`** payload.
Live cycle-1 measurement (PN5/PN6) established it is ALSO reachable by an
ordinary `str`: `CreateCheckType("   ")` strips to `""`, passes the
None-only `_ValidateParam`, and persists an empty name with no exception
(see C7). The exposure is strictly WIDER than the row states -- no type
error on the caller's part is required to lose the entire payload. The row
is preserved verbatim as an audit trail and MUST NOT be rewritten; this
correction is recorded as an APPENDED annotation beneath it.

### C11 -- Per-site fix SHAPE is chosen by the site's own upstream guard, and the three-site whitespace-only carve-out

Grounded in T2's cycle-2 finding and re-verified against HEAD:
`BaseOperations._ValidateParam` (`:3014` at time of writing) is a `None`
check plus a stale-LCM-reference guard and NOTHING else -- no type check,
no empty-string check.

**(a) Two authorised shapes. Which one a site takes is determined by what
validates the argument BEFORE the `.strip()` line:**
- **Shape A -- delete the rebinding outright.** Authorised ONLY where the
  site already calls `_ValidateStringNotEmpty` (or another guard that
  raises on non-`str`) before the `.strip()` line. Used by T1 at
  `DiscourseOperations.CreateChart` and `SetChartName`.
- **Shape B -- keep a throwaway, NON-REASSIGNING `name.strip()`.**
  REQUIRED where the only upstream guard is a null-check-only
  `_ValidateParam`, because there `.strip()` ITSELF is what raises
  `AttributeError` for a non-`str` payload. Deleting it would silently
  remove an existing loud error and change its type -- which C7(b)
  forbids. Used by T2 at `TextOperations.SetName`.

Choosing the wrong shape is a CONTRACT VIOLATION, not a style choice. Read
the site's actual guard at HEAD before editing; never infer it from a
sibling method or from another family's landed diff.

**(b)** A trailing `self._ValidateParam(name, "name")` that becomes a
verbatim duplicate of the leading call on the same unmodified value, once
the rebinding between them is removed, is DEAD and is deleted. The
**leading** `_ValidateParam` is always KEPT (C7a).

**(c) Whitespace-only carve-out at the three Shape-B sites.** At
`AnthropologyOperations.Create`, `AnthropologyOperations.CreateSubitem`,
and `TextOperations.SetName`, a whitespace-only `str` today strips to `""`
and is persisted with NO exception, because `_ValidateParam` is null-only.
This is Q-242B's bug shape at sites the frozen contract never enumerated --
C7's three-way split classified sites by their NON-STR behaviour only and
did not classify their whitespace-only behaviour. Removing the rebinding
necessarily changes the stored value from `""` to the caller's actual
whitespace; "leave it exactly as-is" is not an available option.

**This feature does NOT add a whitespace-only rejection at these three
sites.** Grounds: adopting `_ValidateStringNotEmpty` there IS the
validator-harmonisation decision that **Q-242C owns**, and these three are
precisely the three sites C7(b) names as Q-242C's; deciding half of it here
would fragment that decision across two features. The pre-existing
blank-name-row state is neither created nor worsened by this feature -- it
changes only WHICH invisible string is stored, and it removes a payload
loss (`""`) in favour of raw-byte persistence, per C3.

This does **not** overturn lex-domain's Q6, which is scoped to C7's
`CheckOperations` sites; it declines to EXTEND Q6 to three sites C7(b)
explicitly fences into Q-242C. `CheckOperations` is NOT carved out -- C7
already rules its whitespace-only path loud, and Q6 governs there.

Recorded as **Q-242D**, an UNAUTHORISED candidate awaiting user approval.
T5's CHANGELOG entry must disclose it as a known remaining gap.

### C12 -- CONCURRENCY.md AMENDMENT 2 is EVIDENCED, not merely retained; promotion into the campaign `hard_rules` is the MAIN SESSION's action

**Ruled by `/lex-lead` at the cycle-4 close, on a real incident, one cycle after
authoring the amendment it evaluates.**

**(a) AMENDMENT 2 is RETAINED and remains binding on every remaining task of
this feature, unchanged in wording.**

**(b) It is now EVIDENCED, and the evidence is stronger than cycle 3's.** On
T4's fourth commit, the step-3 check -- `git status --porcelain` re-run
immediately BEFORE `git commit` -- found FIVE of the other crew's
`specs/feature-structure-sync-gap/` files already sitting in the shared index
with staged markers, placed there by their own `git add` in the window after
T4's `git add`. T4 cleared them with an index-only `git reset HEAD -- <five
paths>` (zero working-tree bytes), re-confirmed, then committed. `/lex-lead`
independently confirms `f5291e9` contains exactly one file.

The distinction between the two incidents is the whole point and must not be
flattened in any later summary:
- **Cycle 3 (T3)** -- the race was caught **AFTER** the bad commit, by step 4
  (`git show --stat HEAD`), and required a `git reset --soft HEAD~1` rewind.
- **Cycle 4 (T4)** -- the race was caught **BEFORE** the commit, by step 3, and
  required no rewind at all.

Step 3 is therefore not redundant belt-and-braces on step 4; it is the step
that converts a post-hoc correction into a prevention. The amendment caught, at
exactly its intended catch point, the exact failure that motivated it.

**(c) Step 6's report-even-when-clean requirement is what surfaced this.** T4's
disclosure is the only reason the save is on the record at all. The
requirement stands and is not relaxable: a task that stays silent about steps 3
and 4 has not performed them, regardless of how its commit turned out.

**(d) PROMOTION RECOMMENDATION -- for campaign items 3 and 4, executed by the
MAIN SESSION only.** AMENDMENT 2 should be copied **verbatim** into
`specs/tier1-silent-data-loss/.crew-handoff.json`'s `hard_rules`, so that
campaign queue items 3 and 4 inherit it without re-deriving it from this
feature's incident history. This is recorded as a recommendation, not as work
this feature performs.

**No agent acting inside `name-field-whitespace-identity` -- including T5 and
any archivist pass -- may edit `specs/tier1-silent-data-loss/.crew-handoff.json`
to carry this out.** That file is fenced as the main session's to maintain (see
this feature's standing hard constraints). The promotion is the main session's
action, to be taken when it closes sub-item 2a. If the main session declines
it, the recommendation stands on the record unactioned; it does not lapse and
does not authorise anyone else to perform it.

**(e) This item authorises no loosening.** AMENDMENT 2 having proven its worth
is grounds for extending it, never for concluding that the underlying staging
rule is now sufficient on its own.

### C13 -- T4's offline-baseline order slip: the delta STANDS AS MEASURED, and the load-bearing outcome is the STASH PATHSPEC RULE

**Ruled by `/lex-lead` at the cycle-4 close, on T4's own self-disclosure.**

**(a) What happened.** T4 made its `CheckOperations.py` code edit BEFORE
recording the "before" offline baseline, against the task's STEP 4 ordering. It
recovered by stashing its own edit, measuring the true pre-edit tree, then
restoring the edit with `git stash pop`.

**(b) ACCEPTED. The reported offline delta `+0/+0/+5` stands as measured. No
re-derivation is ordered.** Four independent grounds:
1. The stash/measure/pop produced a genuine before/after pair at the same
   `HEAD` -- a measurement, not a reconstruction from memory or from a prior
   spurt's figures.
2. The C28 predict-before-measure guarantee is INTACT: the predictions commit
   `2d8bfc5` landed before the measuring run. C28 governs predictions versus
   measurement, and was not breached; STEP 4 governs edit versus baseline, and
   was.
3. The `+5` is corroborated out-of-band, independently of the offline run, by
   the live collect count moving 15 -> 20 -- exactly the five new
   `requires_live_project` tests claimed.
4. `git stash list` and the stash reflog were BOTH confirmed empty afterward, so
   the pop was complete and nothing was left parked.

The delta is additionally trustworthy only because the three known-foreign
failures were unchanged by name and message across both measurements, with no
fourth appearing. Under the DELTA rule a measurement taken while the other
crew's uncommitted work sits in the tree is valid precisely because that noise
is expected to be constant across the pair; **if the foreign failure set had
moved between the "before" and "after" runs, the delta would have been VOID and
acceptance would not have been available.**

**(c) THE FORWARD RULE -- this, not the ordering slip, is the actual latent
hazard.** A future agent reading only "the delta was accepted" would take
entirely the wrong lesson. The dangerous artefact of what T4 did was not the
order of operations; it was the recovery mechanism.

**`git stash` with an explicit pathspec -- `git stash push -- <your own path>`
-- is the ONLY authorised form in this clone. A BARE `git stash` (and likewise
`git stash -u`, `git stash --all`, or `git stash push` with no pathspec) is
FORBIDDEN, at the same level as `git reset --hard`.** A bare stash operates on
the entire working tree, which in this shared clone means it would sweep the
other crew's uncommitted, unrecoverable in-flight work into a stash they do not
know exists -- the exact destruction the staging rule and AMENDMENT 2 exist to
prevent, arrived at from a different direction. That it happened to be
recoverable this time is luck, not design.

Attendant obligations whenever a pathspec'd stash is used:
- Stash ONLY paths you authored. Never stash, `checkout`, or `restore` a path
  you did not author -- this restates the standing rule and does not soften it.
- Confirm `git stash list` is EMPTY before finishing the task, and report that
  it is.
- Never use a stash to "tidy" or "clean" the working tree, and never carry a
  stash across a checkpoint boundary or a handoff.

**(d) Ordering preference, unchanged.** Measure the "before" offline baseline
BEFORE the first edit. That is free, and it is still the required order; C13
does not relax STEP 4. The pathspec'd stash is a RECOVERY for a slip already
made, not a routine substitute for correct sequencing.

**(e) If recovery is not cleanly available, the answer is not a
reconstruction.** An agent that has slipped and cannot obtain a genuine
pre-edit measurement with a pathspec'd stash must report the baseline as
unmeasured -- `FAIL: unverified` on that gate, or `needs_human` -- and must NOT
substitute a remembered figure, a prior spurt's absolute (already VOID under
the DELTA rule), or a reconstruction. Honest self-disclosure of the slip, which
T4 did, is what made acceptance possible here and is expected in every
comparable case.

---

## 3. Recorded but not ruled -- an unrelated bug found in cycle 1

**`CheckOperations._GetCheckList()` is a hardcoded stub that always
returns None** (`flexicon/code/System/CheckOperations.py:1168-1179`).
This forces `_GetOrCreateCheckList()` (`:1181-1205`) to always take its
"create a new list" branch, which calls
`self.project.project.ServiceLocator.GetInstance(ICmPossibilityListFactory)`
at `:1198` -- but `ILcmServiceLocator` has no `GetInstance` method; every
other call site in this same file (`:209`, `:1391`, `:1430`) and every
other Operations class in this codebase uses `.GetService(...)`.
**Effect: `CreateCheckType()` raises `AttributeError` on every call, for
every payload, str or not -- it appears to have never worked against a
live LCM.**

This is orthogonal to the name-field whitespace/identity question and
was **NOT fixed** by cycle 1 (zero `flexicon/` lines touched); it was
worked around at the test-instance level only, via a fixture-local
monkeypatch of `_GetCheckList` in the probe file
(`tests/operations/test_name_field_identity_probe.py`'s
`_seed_valid_check_list()`), which does not touch any file under
`flexicon/`.

**This is a candidate queue ask, recorded as an open question, NOT filed
as a GitHub issue and NOT fixed here.** It has one direct consequence for
this feature's own task list, stated plainly so it is not rediscovered
mid-task: **every live task that needs to reach `CreateCheckType`'s own
name-handling logic through the public API (i.e. every Q-242A/Q-242B task
touching `CheckOperations.py`) must use the same test-instance-only
`_GetCheckList` monkeypatch, or it cannot be live-verified at all.** This
is a live-verification dependency, not a design blocker -- the fix itself
(C4/C7) never calls `_GetOrCreateCheckList`, so it is unaffected by the
bug; only the test harness needs the workaround.

---

## 4. Contradictions checked for

The cycle-1 programmer report and evidence file, and the cycle-1 domain
ruling, were checked against C1-C8 (as received from `/lex-lead` and
transcribed above) for contradictions. **None found.** All binding
predictions (PN1-PN4, PN7, PN8's binding claim) MATCHED. The one
non-binding MISS (PN8's sub-detail on byte-identity of the second
duplicate record) is a measurement artifact of testing against
pre-C4-fix code, explicitly flagged as non-binding by the programmer
before the run, and is folded into C2 above as a correction note, not
treated as a contradiction. `/lex-domain`'s ruling independently
re-derived C3's answer rather than merely restating it, and its
conclusion agrees with `/lex-lead`'s option (i) in substance.

---

## 5. Open questions

**None left genuinely open inside this feature's scope.** C1-C8 are
frozen; Q-242C (coercion harmonisation) remains explicitly out of scope
per C7(b) and stays queued in `specs/tier1-silent-data-loss/QUEUE.md`
"Awaiting user approval," untouched by this feature. The
`CheckOperations._GetCheckList()` bug (section 3 above) is recorded, not
ruled on, and not a task.

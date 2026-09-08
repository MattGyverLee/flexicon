# SPEC -- name-field-whitespace-identity

**Repo:** flexicon, branch `main`
**Issues:** flexicon#242 (parent whitespace campaign), sub-items Q-242A and
Q-242B of `specs/tier1-silent-data-loss/QUEUE.md`
**Campaign:** `tier1-silent-data-loss`, spun-out sub-item **2a** (between
queue item 2, `242-paragraph-whitespace`, and queue item 3,
`feature-structure-sync-gap`)

**Status:** CHECKPOINT 3, 2026-09-07. **This header was stale and is
corrected here (C27): it previously read "no behaviour change under
`flexicon/code/` has been authorised by THIS feature yet", which was true
only at cycle 1.** Behaviour changes HAVE landed. All 8 persist sites and
all 3 comparison sites are fixed and committed by this feature, across
four files:
`flexicon/code/TextsWords/DiscourseOperations.py` (T1, `3eac4a0`),
`flexicon/code/TextsWords/TextOperations.py` (T2, `db95230`),
`flexicon/code/Notebook/AnthropologyOperations.py` (T3, `ab638aa`), and
`flexicon/code/System/CheckOperations.py` (T4, `0ab9c60`). Docs landed at
T5 (`90cfce7`). Every site is live-verified EXCEPT
`DiscourseOperations.CreateChart`'s persist half, which is
**`FAIL: unverified`** (Q-DISC1) -- inspection-correct but unreachable
through its own public API. **This feature does not claim 8/8 verified.**

Unrelated modifications under `flexicon/code/BaseOperations.py` and
`flexicon/code/Grammar/` belong to the second, concurrent crew described
in `CONCURRENCY.md` and are NOT this feature's work; do not attribute them
here, do not stage them, do not revert them.

Contract items C1-C13 below are FROZEN, transcribed substantially verbatim
from the rulings that authorised and governed this feature. `tasks.md`
derives the implementation tasks from them.

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

**MERGED FILE -- READ APPENDIX A FIRST.** A second crew wrote this same
spec independently on `origin/main` (PR #282) using an `NF1-NF11`
numbering. Both documents are preserved here: sections 0-5 (`C1-C13`)
below, then **Appendix A** (what each side is authoritative for, and the
`#242` auto-close) and **Appendix B** (the `NF1-NF11` ruling, verbatim).

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

**(f) EXTENSION, ruled at the sub-item 2a closure (after C12 was first
frozen).** C12(d)'s promotion recommendation was authored BEFORE
`CONCURRENCY.md` AMENDMENT 3 existed. It is extended to cover **AMENDMENT 2 and
AMENDMENT 3 together, promoted as a single unit**, on the grounds that they are
one protocol and not two: AMENDMENT 2 brackets the commit, AMENDMENT 3 closes
the working-tree-destruction gap that the bracket does not reach. Promoting 2
alone would export the commit-time race protection to campaign items 3 and 4
while leaving them exposed to the bare-`git stash` hazard that C13(c) exists to
prevent -- and those items run in the SAME shared clone, against the SAME second
crew, and will perform the SAME offline-baseline measurement step that occasioned
T4's slip. All other terms of C12(d) are unchanged: the promotion is the MAIN
SESSION's action, into `specs/tier1-silent-data-loss/.crew-handoff.json`'s
`hard_rules`, verbatim, and no agent acting inside this feature may perform it.

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

---

## Appendix A -- MERGE RECONCILIATION, 2026-09-08 (origin/main, PR #282)

**Two crews wrote this file independently, and it arrived as an add/add
conflict when local `main` (120 commits ahead) merged `origin/main`
(11 commits ahead, PR #282).** Neither side was wholesale correct, so
neither was discarded. Resolution, and what each side is authoritative
for:

- **Sections 0-5 above (`C1-C13`) are authoritative on IMPLEMENTATION
  STATUS.** The work described there really did land: the six cited
  commits (`3eac4a0`, `db95230`, `ab638aa`, `0ab9c60`, `90cfce7`,
  `5c161e1`) were verified at merge time to exist and to be ancestors of
  local `main`. The four touched Operations files came through the merge
  with the name-field fixes intact; the incoming edits to three of them
  (`AnthropologyOperations`, `CheckOperations`, `DiscourseOperations`)
  were the unrelated #270/#272 casting work and did not overlap.

- **Appendix B below (`NF1-NF11`) is the other crew's ruling document,
  preserved verbatim.** It is dated LATER (2026-09-08) yet states
  "Implementation has NOT started. `git diff --stat -- flexicon/` is
  empty for this feature." **That statement was true on its own branch
  and false on `main`**: `spec/242-gate-and-name-field-identity` was cut
  from an `origin/main` that was 120 commits behind, so the
  implementation commits were invisible to it. Do not read it as a
  retraction of the work above. It is kept because
  `specs/tier1-silent-data-loss/QUEUE.md` cites "NF1-NF11" by name, and
  because it carries tracker facts sections 0-5 lack (see below).

- **The two crews ruled the central question IDENTICALLY.** C3 above and
  NF3 in Appendix B both hold that whitespace is not identity-bearing for
  name fields, that names are stored verbatim, and that comparison runs on
  a normalized key. There is no contract conflict to adjudicate -- only
  duplicate numbering.

- **Appendix B is authoritative on ISSUE-TRACKER STATE**, which sections
  0-5 predate: Q-242B was approved and filed as **flexicon#273**, Q-242A's
  blocker was discharged and filed as **flexicon#274**, and **#242 was
  auto-closed** (`CLOSED`/`COMPLETED`, 2026-09-07T19:25:16Z, by the
  `closes #242` keyword in commit `066bab0`) against the recorded
  "closes nothing" policy. `#242`'s open/closed disposition is a USER
  decision and was deliberately not reversed by this merge.

**Citation convention, now that both schemes are in one file:** this
feature's own items remain bare `C1..C13`. Cite the other crew's items as
**"NF-n (Appendix B)"**, never bare `NF-n`.

---

## Appendix B -- the parallel `NF1-NF11` ruling document, verbatim

Reproduced from `origin/main` (`dd5422f`, PR #282) exactly as written, with
heading levels demoted one step to nest under this appendix. No wording was
changed. Read its status header in light of Appendix A: its claim that
implementation had not started reflects its branch, not `main`.


**Repo:** flexicon, branch `main`
**Origin:** Q-242A in `specs/tier1-silent-data-loss/QUEUE.md`, routed there by
`specs/242-paragraph-whitespace/spec.md` C10 (`/lex-lead`'s R3 ruling).
**Campaign:** `tier1-silent-data-loss` -- related to queue item 2 (#242),
NOT a queue item itself.

**Status: THE DEDUP-IDENTITY QUESTION IS RULED, 2026-09-08 (NF3-NF6).**
That ruling was the stated blocker on Q-242A ("The blocker is a name-field
identity ruling, not effort"), so Q-242A is now UNBLOCKED.

**Implementation has NOT started.** `git diff --stat -- flexicon/` is
empty for this feature. The environment blocker is RESOLVED as of
2026-09-08 (#242's C19), so implementation is actionable -- see NF8 for the
required order of work.

Contract items **NF1-NF11** below are FROZEN. They use an `NF` prefix
deliberately so they can never be confused with #242's `C1-C18` when cited
across features.

---

### 1. The question, as filed

From Q-242A, verbatim: preserving the unstripped payload at the 8 name-field
writer sites would leave an unanswered question --

> "is `"Genesis "` the same text as `"Genesis"`?"

-- that #242's own four filed sites never had to answer, because none of
them has a name-uniqueness check.

**The question as filed contains a false premise**, corrected by NF2: it
presents the identity question as something *created* by fixing the strip.
It is not. The identity defect is live and reachable through this library's
own public API today, with the strip fully in place.

---

### 2. Contract items

#### NF1 -- The census (FROZEN finding of fact)

Source: cycle-1 census, 2026-09-08, static analysis of every
`normalize_match_key` reference under `flexicon/`. Independently derived,
not copied from the Q-242A brief.

`normalize_match_key` (`flexicon/code/Shared/string_utils.py:50-82`) applies
`normalize_text` -> NFD -> optional `casefold`. **It performs no whitespace
handling of any kind.** Its own docstring declares it the both-sides
normalizer: *"Apply this to BOTH sides of any Find/Exists comparison."*

117 raw grep hits decompose into 34 `import` lines, 3 definition/docstring
lines, 1 comment, and **80 actual call expressions forming exactly 40
comparison pairs** (no site has an odd call).

| Bucket | Meaning | Count |
|---|---|---|
| **A -- ASYMMETRIC** | needle stripped, haystack raw | **10** |
| **B -- SYMMETRIC-UNSTRIPPED** | neither side stripped | **30** |
| **C -- SYMMETRIC-STRIPPED** | both sides stripped | **0** |
| **D -- not a comparison** | key used for sorting/dict/etc. | **0** |

**Bucket A is exactly 10/40 = 25% of all comparison sites**, and is confined
to six method names -- `Exists`, `Find`, `FindByName`, `FindList`,
`FindItem`, `FindCheckType`. Every member is a name-keyed lookup or
existence entry point; **not one is a setter or a getter.** The defect lives
entirely on the read-by-name surface. Name for the shape: the
**stripped-needle lookup family.**

The ten bucket-A sites (needle line / haystack line / method):

| Needle | Haystack | Method |
|---|---|---|
| `Lexicon/SemanticDomainOperations.py:230` | `:236` | `FindByName` |
| `Lists/AgentOperations.py:280` | `:285` | `Find` |
| `Lists/PossibilityListOperations.py:326` | `:332` | `FindList` |
| `Lists/PossibilityListOperations.py:850` | `:856` | `FindItem` |
| `Lists/possibility_item_base.py:293` | `:298` | `Find` |
| `Notebook/AnthropologyOperations.py:562` | `:565` | `Find` |
| `Notebook/LocationOperations.py:312` | `:318` | `Find` |
| `Shared/FilterOperations.py:361` | `:364` | `Find` |
| `System/CheckOperations.py:344` | `:350` | `FindCheckType` |
| `TextsWords/TextOperations.py:461` | `:464` | `Exists` |

**`casefold` divergence between needle and haystack: 0 sites.** Every pair
passes the same value on both sides. There is no second asymmetry bug of
that kind, and this item records the negative result so nobody re-hunts it.
(There *is* a policy inconsistency -- 21 sites case-insensitive, 19
case-sensitive -- but each site is internally consistent. Out of scope; see
NF6.)

Haystack producers were verified non-stripping by reading each, not by
pattern-matching: `ITsString(...).Text`, `best_analysis_text`
(`string_utils.py:160-180`), `InflectionClassGetName`
(`InflectionFeatureOperations.py:337-338`), `PhonologicalRule.name`
(`Grammar/phonological_rule.py:132-137`), `mdc.GetFieldLabel`
(`CustomFieldOperations.py:166`), `_LoadFiltersFromProject`
(`FilterOperations.py:1031-1050`), and `parse_etic_gloss_list`
(`Shared/catalog.py:247-250`).

#### NF2 -- The defect has TWO halves, and BOTH are reachable through this library's own public API today

This item corrects the false premise in the question as filed (section 1).

**Half one -- the duplicate explosion (4 sites).** A `Create` strips the
name, asks its uniqueness guard about the *stripped* value, and the guard
consults a bucket-A lookup that never strips the haystack. A stored padded
name is therefore invisible to the guard, which does not fire:

1. **`TextOperations.Create`** -- strip `:152`, guard `:155
   if self.Exists(name):`, persists stripped at `:171-172`. Also
   **`TextOperations.Duplicate:293`** -- `while self.Exists(new_name):`
   drives the `" (copy N)"` uniqueness loop through the same blind guard,
   so it can hand `Create` a name that already exists in padded form.
2. **`AnthropologyOperations.Create`** -- strip `:264`, guard `:269
   if self.Exists(name):` -> `:510 return self.Find(name) is not None`.
3. **`CheckOperations.CreateCheckType`** -- strip `:195`, guard `:200
   if self.FindCheckType(name):`, persists stripped at `:218-219`.
4. **`FilterOperations.Create`** -- guard `:231 if self.Find(name) is not
   None:`, persists `"name": name.strip()` at `:251`. **Least exploitable
   of the four**, recorded honestly: every filter created through this
   method is stored already-stripped, so a padded haystack can only enter
   via legacy or external writes to the `flexlibs_filters` JSON.
   `FilterOperations.ImportFilters:897/:901` reuses the same blind guard
   for its auto-rename loop.

**Half two -- the unreachable object (5 sites). This is the half that
refutes the premise.** Five `Create` methods persist the **raw, unstripped**
name and have **no uniqueness guard at all** (they guard only
`if not name or not name.strip()` for emptiness), and each is paired with a
bucket-A lookup:

- `Notebook/LocationOperations.py:195` (paired with `Find` `:312`/`:318`)
- `Lists/possibility_item_base.py:200` (paired with `Find` `:293`/`:298`)
- `Lists/PossibilityListOperations.py:234` `CreateList` (paired with
  `FindList` `:326`/`:332`)
- `Lists/PossibilityListOperations.py:533` `CreateItem` (paired with
  `FindItem` `:850`/`:856`)
- `Lists/AgentOperations.py:178` (paired with `Find` `:280`/`:285`)

Consequence, stated plainly:

> **This library can create an object through its own public API that it
> can then never find by name.** `Create("Genesis ")` stores `"Genesis "`;
> `Find("Genesis")` strips the needle and misses; `Find("Genesis ")` strips
> the needle to the same thing and misses identically. The object is
> unreachable by name through every lookup the library offers.

No external writer, no FLEx UI, no import and no direct LCM write is
required. **The identity defect is therefore PRE-EXISTING and INDEPENDENT
of #242's fix**, not a consequence of preserving whitespace -- the same
classification C12 reached for the `AppendSentence` join boundary, on the
same reasoning.

#### NF3 -- RULING: whitespace is NOT identity-bearing for name fields; case remains as each site has it

**Ruling, 2026-09-08.** For the purpose of name identity, uniqueness and
lookup: **`"Genesis "` IS the same name as `"Genesis"`.** Leading and
trailing whitespace is incidental padding, never identity.

Grounds, in order of weight:

1. **It is invisible.** Trailing whitespace cannot be seen in the FLEx UI.
   Two objects distinguishable only by it are indistinguishable to the user
   who has to work with them -- a data-quality trap, not a distinction the
   API should honour.
2. **The codebase already agrees, implicitly and at scale.** 30 of the 40
   comparison sites open with `if not X or not X.strip(): return None` --
   they already treat a whitespace-only needle as no needle at all. Ruling
   whitespace non-identity-bearing makes an existing majority convention
   explicit rather than importing a new idea.
3. **No site depends on the opposite.** The census hunted specifically for
   a comparison where leading/trailing whitespace is genuine data and
   **found none** (NF1's methodology, checked concretely per domain).
   Interior spaces in multi-word lexemes, glosses and titles are untouched
   by `.strip()`; FLEx models phonological boundaries as `PhBdryMarker`
   objects with `#`/`+` representations, not as space characters, so even
   IPA representations carry no meaningful edge whitespace.

**Case is ruled differently, and deliberately so.** Case stays exactly as
each site has it today (21 case-insensitive, 19 case-sensitive; NF1).
Case is *visible and intentional* where edge whitespace is neither, so the
two do not follow the same rule. Harmonising the case-sensitivity policy is
explicitly OUT of scope (NF6) -- this ruling must not be cited as
precedent for it.

#### NF4 -- RULING: identity and storage are separate concerns; the code conflates them

**Ruling.** The apparent conflict between this feature and #242's C8
("persist the caller's original, unstripped value") is not real. It
dissolves once two questions are separated:

| Question | Answer | Governed by |
|---|---|---|
| What do we **store**? | The caller's payload, **verbatim** | #242 C8 |
| What do we **compare**? | A **normalized key** | NF3 / NF5 |

**Store verbatim; compare normalized.** These are complementary, not
opposed. The present code conflates them by computing ONE stripped local
and using it for BOTH purposes -- that single conflation is the root cause
of both halves of NF2 and of the name-field data loss Q-242A was filed
about. Fixing the conflation fixes all three at once.

This is why the ruling is not a trade-off between fidelity and dedup. The
`preserve_whitespace=`-style flag rejected by #242 C8 as the
caller-managed-flag anti-pattern is likewise not needed here, and for the
same reason: correct behaviour is unconditional, not a caller's choice.

#### NF5 -- RULING: the normalization lives INSIDE `normalize_match_key`

**Ruling (user decision, 2026-09-08).** Whitespace stripping is added
**inside `normalize_match_key`**, applied to whatever passes through it, so
needle and haystack are normalized identically by construction. Call sites
in bucket A then **drop** their needle-only `.strip()`.

**Grounds:** the function's own docstring already declares it the
both-sides normalizer for Find/Exists comparisons, and it already handles
NFD and casefold symmetrically. Whitespace is the one normalization that
leaked outside it and so got applied to one side only. Putting it inside
does not add a concept -- it finishes an existing one.

**Decisive property: correct-by-default for future code.** A new
`Find`/`Exists` written next year gets symmetric matching for free. The
per-call-site alternative was considered and REJECTED: it is 10+ separate
edits, risks a missed site, and leaves the buggy shape as the default that
new code will keep reproducing. Bucket B's 30 symmetric-unstripped sites
are additionally brought into line at no extra cost, since both their sides
route through the same function.

**Blast radius accepted knowingly.** This is shared code with 80 call
sites; CLAUDE.md requires consultation before changing shared utilities,
and that consultation happened -- this item records the decision, not an
assumption.

**REFINED, 2026-09-08, after the impact assessment (user ruling).** The
unconditional form of this ruling had a provable counter-example, found by
the blast-radius pass and confirmed by direct measurement (NF11). The
binding shape is therefore the shared strip **plus a fence**, subject to
four conditions, all four BINDING:

1. **Placement:** `text = normalize_text(text).strip(" \t\r\n")` --
   **after** the `FLEX_NULL_MARKER` check, before the `if not text: return
   ""` early exit. See NF7 H4 for why placement is load-bearing rather
   than stylistic.
2. **Character set:** `.strip(" \t\r\n")`, **NOT** bare `.strip()`.
   See NF7 H5 -- bare `.strip()` silently discards U+00A0 NBSP and U+3000
   from vernacular data, a semantics decision this ruling declines to make.
3. **The containment site is FENCED OFF the shared helper.**
   `ScrDraftOperations.Find` does a substring match, not an equality match,
   and must not borrow the equality key. See NF7 H2.
4. **Needle guards** are added at the sites that currently have none, so a
   whitespace-only needle cannot degenerate into the promiscuous `""` key.
   See NF7 H6.

**The principle behind condition 3, stated so it generalises:**
`normalize_match_key` is the **equality** normalizer -- its own docstring
scopes it to "any Find/Exists comparison". Containment is a *different
operation* with different requirements: for a substring search, edge
whitespace is the only word-boundary anchor the API offers. Fencing the
containment site is therefore not a patch around an inconvenience; it is
the correct recognition that two different operations were sharing one
helper. Any future containment search must likewise not use this helper.

#### NF6 -- RULING: scope is the matcher plus the 8 filed sites

**Ruling (user decision, 2026-09-08).**

**IN scope:**
1. `normalize_match_key` -- strip both sides (NF5).
2. Bucket A's 10 sites -- drop the now-redundant needle-only `.strip()`.
3. The 8 Q-242A writer sites -- stop stripping before persist, using #242
   C8's binding shape (`x = v if isinstance(v, str) else str(v)`; guard on
   `x.strip()`; persist the ORIGINAL `v`).
4. NF2's two halves fall out of 1-3 together: uniqueness guards begin to
   fire correctly, and created objects become findable.

**OUT of scope, and staying queued:**
- **Q-242B** -- `CheckOperations.py:196/:341/:432`, where a non-`str`
  payload becomes a silently persisted EMPTY name. Filed separately and
  flagged MORE SEVERE precisely so it is not triaged at whitespace
  severity; folding it in here would undo that. Note NF1 records
  `CheckOperations.py:341` as a bucket-A site, so this feature touches that
  FILE -- it does not touch the coercion defect.
- **Q-242C** -- `BaseOperations._ValidateParam` coerce-vs-reject. A public
  API-surface decision across 12+ sites.
- **The case-sensitivity policy inconsistency** (21 vs 19 sites, NF1).
  Newly documented by this census, ruled out of scope by NF3, and NOT
  queued as a defect -- each site is internally consistent, so this is a
  consistency question, not a bug.

#### NF7 -- Mechanics and the hazards any implementation must respect

Recorded as binding constraints on the implementation, ahead of it. H2, H4,
H5 and H6 are the four conditions NF5 makes binding.

**H1 -- `strip_display_marker` is not a whitespace strip.**
`flexicon/code/Shared/morph_type_utils.py:91` is
`return name.strip("-=~<>")`. With a character-set argument, `str.strip`
removes **only** those characters and no whitespace -- so `:108-109`'s
`bare = strip_display_marker(name)` reads like a strip but is not one
(correctly bucket B). It carries a **pre-existing ordering defect
independent of this feature**: a needle of `" -suffix"` keeps its `-`
marker, because the leading space blocks the marker strip. **Whitespace
must be stripped BEFORE marker stripping** for that call to be correct.
Putting the strip inside `normalize_match_key` does NOT fix this, because
`strip_display_marker` runs first, at the call site -- so H1 remains OPEN
after this feature. Recorded, not resolved.

**H2 -- `ScrDraftOperations.Find:272` is containment, not equality.
RESOLVED BY FENCE (NF5 condition 3).**

```python
target = normalize_match_key(description, casefold=True)
...
if target and target in normalize_match_key(draft_desc, casefold=True):
```

The only `in` comparison among the 40 pairs; its docstring at `:252` says
"Partial match searches entire description". Measured directly,
2026-09-08:

```
needle " draft" in "redrafted genesis" : False     <- today
needle  "draft" in "redrafted genesis" : True      <- after an unfenced strip
```

So an unfenced shared strip **silently widens this search predicate** -- a
needle that correctly missed now matches. This site is fenced off the
shared helper per NF5 condition 3, and must NOT be swept into a mechanical
rewrite. Its whitespace-only needle is already guarded at `:258-259`.

**H3 -- whitespace-only needles change behaviour; state it, do not assume
it benign.** Because `normalize_match_key` does not strip today, a `"   "`
needle yields a TRUTHY key; afterwards it yields `""`. Sites guarding
`if not target:` begin to fire that guard --
`InflectionFeatureOperations.py:551` and `:605`,
`NaturalClassOperations.py:226`, `PhonFeatureOperations.py:247`. For those
the new behaviour is an **improvement**: a whitespace-only needle correctly
matches nothing, instead of comparing a truthy whitespace key. The
unguarded sites are H6.

**H4 -- `FLEX_NULL_MARKER` placement. RESOLVED (NF5 condition 1).**
`normalize_text` maps the bare `'***'` to `""` by **exact equality**
(`string_utils.py:46`), so placement decides the padded marker's fate:

| input | today | strip AFTER `normalize_text` (BINDING) | strip BEFORE (WRONG) |
|---|---|---|---|
| `"***"` | `""` | `""` | `""` |
| `" *** "` | `" *** "` | `"***"` | `""` |
| `"   "` | `"   "` | `""` | `""` |

**Ruling: strip AFTER `normalize_text`.** `" *** "` normalizes to `"***"`,
NOT to `""`. The rejected ordering is not merely different, it is
**wrong**: `""` is the key every unset LCM field produces
(`normalize_text(None) == ""`), so collapsing a padded marker into it
manufactures a collision between real data and the empty bucket -- an item
literally named `" *** "` would be returned by a `Find` for any empty-ish
needle. This is the one piece of mechanics the original ruling left open;
it is now closed.

**H5 -- bare `.strip()` is too wide for a linguistics library. RESOLVED
(NF5 condition 2).** `str.strip()` with no argument removes all Unicode
whitespace, including U+00A0 NBSP and U+3000 IDEOGRAPHIC SPACE
(`'\xa0'.isspace()` is `True`). The haystacks here include vernacular
forms, glosses and phoneme representations; silently discarding an edge
NBSP from that data is a semantics decision **nobody has made**, and this
ruling declines to make it. **Binding: `.strip(" \t\r\n")`**, which
reproduces exactly the intent of the legacy call-site strips and rules on
nothing further. Whether real project data carries edge NBSP is **UNKNOWN**
-- it needs a live read (NF8), and is exactly the kind of question that
must not be settled by a default.

**H6 -- the empty-key false-positive hazard. Guards REQUIRED (NF5
condition 4).** With stripping inside, a whitespace-only needle yields
`target = ""`, which is the key of every unset field. Sites where neither
the needle is whitespace-guarded nor the haystack truthiness-guarded would
then return the first object with an empty name:

- `Grammar/PhonemeOperations.py:462-478` (`Find`) -- `_ValidateParam` is a
  None-check only
- `Grammar/PhonologicalRuleOperations.py:332-337` (`Find`)
- `Grammar/POSOperations.py:343-352` (`Find`)
- `Notebook/DataNotebookOperations.py:479-487` (`Find`)
- `Grammar/PhonemeOperations.py:929-936` (`FindCode`) -- guards
  `if code_repr is None: continue` but not `""`; **whether an unset
  `IPhCode.Representation` yields `None` or `""` is UNKNOWN** and needs a
  live read (NF8)

This hazard is **pre-existing in kind** -- today `Find("")` already
produces `target = ""` at these sites -- but the change **widens the
trigger** from the single value `""` to every whitespace-only string. Some
fifteen sibling sites are immune because they already guard the needle
(`if not name or not name.strip(): return None`) or the haystack
(`if feat_name and ...`).

**H7 -- the test suite gives NO signal on this change.** Zero tests
anywhere pass a padded needle to any `Find`/`Exists`/`FindItem`/`FindList`/
`FindByName`/`FindCheckType`/`FindCode` (targeted sweep of `tests/`,
2026-09-08). `tests/test_normalize_match_key.py` has **no padded-input case
in either direction** -- not asserting stripping, not asserting
preservation. Three tests whose names suggest whitespace significance are
all false alarms: `test_homographs.py:397-414` and
`test_sense_lookups.py:346-364` compare Mocks with a bare `==` and never
call the helper (and the latter's distinguishing whitespace is *interior*
anyway), and `test_inflection_features.py:607-616` exercises the write
path's emptiness guard. **Binding: new unit cases for `" x "`, `"   "` and
`" *** "` must land WITH the change**, since the existing suite cannot
catch a regression -- and per NF8 cannot even be executed.

**H8 -- nothing persisted or snapshotted shifts.** No
`normalize_match_key` output is persisted anywhere. `FilterOperations` keys
by GUID (`:259`) and stores the name already-stripped (`:485`). The two
non-comparison calls (`PhonemeOperations.py:1799`/`:1850`) are a per-call
local dict, symmetric on both sides, never persisted.
`tests/contract/snapshots/expected_contract.json` records only LCM/`SIL.*`
dependencies; `string_utils.py` is absent from its 79-entry `files` map,
and `grep -o normalize_match_key` against it returns 0. Snapshot
unaffected.

#### NF8 -- Verification gate: BLOCKED, and the cycle-1 predictions are UNMEASURED

**UPDATED 2026-09-08: the environment blocker is RESOLVED.**
`specs/242-paragraph-whitespace/spec.md` **C19** relaxed the pins
(`requires-python >=3.8,<3.15`, `pythonnet >= 3.0.3, <3.2`) on the user's
ruling; `pythonnet 3.1.0` ships a real cp314 wheel, `import clr` succeeds,
and the offline suite executes again at **1291 passed / 483 deselected**.

**Implementation of THIS feature is therefore no longer environment-blocked
-- but it is still UNVERIFIED and unstarted.** What C19 restored is the
ability to run tests; it did not run any test for this feature, because
this feature has no tests yet (see below).

Per CLAUDE.md, live verification is REQUIRED for any change touching an
Operations class, a property setter, or the write path -- and all three are
in scope here. A mock-only pass is `FAIL: unverified`, never a clean
result. **This ruling therefore authorises the fix shape; it does not
authorise reporting the fix as done.**

**State of the cycle-1 predictions, recorded so no future reader
over-reads them:**

- `evidence/live-probe-cycle1.md` holds predictions PN1-PN8, committed
  `bdbce02` before any measurement, per the C28 forward rule. Its RESULTS
  section reads `(pending)`.
- **The predictions are entirely UNMEASURED.** No live run has occurred.
- **The harness it names, `tests/operations/test_name_field_identity_probe.py`,
  DOES NOT EXIST** -- absent from the working tree and from every commit in
  history (`git log --all` returns nothing for that path).

**Consequence:** PN1-PN8 are hypotheses, not evidence, and must never be
cited as measurements. NF1's census is *static* analysis -- it establishes
what the code SAYS, which is sufficient to ground NF3-NF6, and is NOT a
substitute for measuring what the LCM DOES. NF2's two halves are read from
the code and remain unconfirmed against a live database.

**The environment is no longer the blocker (C19).** The order of work
stands unchanged and is now actionable: write the harness, measure PN1-PN8
against the UNFIXED code to confirm the defect empirically, then implement,
then re-measure. Live verification is now possible and therefore REQUIRED
before any part of this feature is reported done.

---

#### NF9 -- Provenance: the asymmetry is legacy residue, not design

`git log -L` on the needle lines establishes that nobody ever decided the
needle should be stripped and the haystack not. Commit `6a2942c`
("fix: NFD-normalize Find/Exists comparisons") converted the sites
mechanically:

```
-        name_lower = name.strip().lower()
+        target = normalize_match_key(name.strip(), casefold=True)
```

and `4ff6344` had introduced the `name.strip().lower()` idiom before that.
The needle-only `.strip()` is therefore **inherited from the pre-NFD
`.strip().lower()` idiom and carried forward unexamined** when
`normalize_match_key` was introduced.

Two consequences, both load-bearing for this ruling:

1. It confirms the asymmetry is a **bug**, not an interface contract, so no
   caller can be presumed to depend on it.
2. It explains the single exception cleanly: `ScrDraftOperations.Find`
   **never had a `.strip()`** to carry forward, which is exactly why its
   unstripped needle is meaningful (NF7 H2). The one site that is correct
   today is correct because it was never touched by the idiom the others
   inherited.

#### NF10 -- A citation defect in #242's C8, recorded for that spec's owner

Found while checking whether a `strip=` kwarg would repeat a rejected
pattern. #242's C8 rejects the `preserve_whitespace=` kwarg as

> "the CLAUDE.md-named caller-managed-flag anti-pattern"

**That attribution cannot be substantiated.** `grep -rn "caller-managed"`
across the repo returns hits ONLY inside `specs/242-paragraph-whitespace/`
(`spec.md:391`, `STATUS.md:106`, `tasks.md:114`). The phrase
"caller-managed-flag anti-pattern" **does not appear in `CLAUDE.md`** at
HEAD, nor anywhere under `docs/`.

**This does NOT overturn C8.** C8's *substantive* reasoning is quotable and
checkable independently of the attribution -- the 82-vs-12 verdict at
`spec.md:295`, i.e. a house convention already existed, so the four filed
sites were outliers and a flag would have let them stay outliers. That
argument stands on its own.

Recorded here because (a) a frozen contract item cites a rule that cannot
be located, and the freeze mechanism depends on citations being checkable;
and (b) it matters directly to NF5 -- see NF11's second entry. The fix
belongs to #242's owner: either locate the rule, write it into `CLAUDE.md`,
or restate C8's ground as the 82-vs-12 argument alone.

#### NF11 -- Disagreements between cycle-1 passes, adjudicated rather than smoothed

Per this campaign's contradiction discipline, disagreements are preserved
with the adjudication shown, not silently reconciled.

**1. Is `ScrDraftOperations.Find` safe under an unconditional strip?**
The census pass said *"stripping both sides is safe here but does not fix
anything."* The blast-radius pass said it is a **provable break**.

**ADJUDICATED IN FAVOUR OF THE BLAST-RADIUS PASS, by direct measurement**
(NF7 H2): `" draft" in "redrafted genesis"` is `False`, `"draft" in
"redrafted genesis"` is `True`. The census pass was wrong; a needle that
correctly missed would begin to match. This single counter-example is what
converted NF5 from an unconditional shared strip into a shared strip **plus
a fence**, and it is the reason condition 3 exists. Recorded prominently
because the ruling would have been wrong without it.

**2. Would a `strip=` kwarg repeat C8's rejected anti-pattern?**
The blast-radius pass argued NO, on two grounds: `normalize_match_key`
**already carries a caller-managed flag** in `casefold=`, genuinely
exercised (41 call expressions pass `True`, 39 pass `False`, 2 take the
default -- a near-even split, so the flag does load-bearing work); and
C8's stated ground (an existing 82-vs-12 majority to conform to) is absent
here, where the split is 10 wrong against 30 that are correct-as-written
and at least one member of the minority is *correctly* unstripped.

**ACCEPTED as reasoning, but MOOT as an outcome.** A kwarg would have to
default to `strip=False` to be non-breaking, at which point every equality
site needs editing anyway and it saves nothing over the per-site fix, while
adding a third dimension to a two-dimensional helper. The kwarg was
therefore rejected on cost, **not** on the anti-pattern -- a distinction
NF10 makes necessary, since the anti-pattern could not be located as a
written rule.

**3. How many asymmetric sites are there -- 10 or 8?**
The census reported **10**; the blast-radius pass tabulated **8** and then
named `AnthropologyOperations.py` and `CheckOperations.py` separately as
"reassignment-style" needle strips.

**RECONCILED: 10 is correct, and the two counts do not conflict.** Seven
sites strip inline in the call expression
(`normalize_match_key(name.strip(), ...)`); three strip by reassigning a
local first (`name = name.strip()`, then the key is built from `name`) --
`TextOperations.py:458/:461`, `AnthropologyOperations.py:558/:562`,
`CheckOperations.py:341/:344`. The blast-radius table folded one
reassignment site into its 8 and listed the other two in prose. 7 + 3 = 10.
**Anyone fixing these must use both greps**, since an inline-only pattern
match silently misses three sites.

### 3. What this ruling unblocks

**Q-242A is UNBLOCKED.** Its stated blocker was this ruling, and the
ruling is now on file (NF3-NF6). `specs/tier1-silent-data-loss/QUEUE.md`'s
Q-242A entry still reads "No work happens on this until the user rules on
the dedup-identity question" -- that line is now satisfied and should be
updated by whoever maintains the campaign record. **This spec does not edit
QUEUE.md**, per #242's constraint that campaign-level files belong to the
main session.

Implementation remains gated on NF8 (the environment), not on any
outstanding decision.

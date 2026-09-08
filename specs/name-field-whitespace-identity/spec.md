# SPEC -- name-field-whitespace-identity

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

## 1. The question, as filed

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

## 2. Contract items

### NF1 -- The census (FROZEN finding of fact)

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

### NF2 -- The defect has TWO halves, and BOTH are reachable through this library's own public API today

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

### NF3 -- RULING: whitespace is NOT identity-bearing for name fields; case remains as each site has it

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

### NF4 -- RULING: identity and storage are separate concerns; the code conflates them

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

### NF5 -- RULING: the normalization lives INSIDE `normalize_match_key`

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

### NF6 -- RULING: scope is the matcher plus the 8 filed sites

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

### NF7 -- Mechanics and the hazards any implementation must respect

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

### NF8 -- Verification gate: BLOCKED, and the cycle-1 predictions are UNMEASURED

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

### NF9 -- Provenance: the asymmetry is legacy residue, not design

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

### NF10 -- A citation defect in #242's C8, recorded for that spec's owner

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

### NF11 -- Disagreements between cycle-1 passes, adjudicated rather than smoothed

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

## 3. What this ruling unblocks

**Q-242A is UNBLOCKED.** Its stated blocker was this ruling, and the
ruling is now on file (NF3-NF6). `specs/tier1-silent-data-loss/QUEUE.md`'s
Q-242A entry still reads "No work happens on this until the user rules on
the dedup-identity question" -- that line is now satisfied and should be
updated by whoever maintains the campaign record. **This spec does not edit
QUEUE.md**, per #242's constraint that campaign-level files belong to the
main session.

Implementation remains gated on NF8 (the environment), not on any
outstanding decision.

# Live verification -- issue #321 (derived-list investigation)

**Project:** Sena 3, disposable temp-directory COPY only (never the real
`C:\ProgramData\SIL\FieldWorks\Projects\Sena 3`)
**Fixture:** none of the repos pytest fixtures -- ran as standalone scripts
(see below) that mirror tests/flex_plugin.py's live-init sequence, because
this task is an ad-hoc experiment rather than a regression test.
**FieldWorks:** FieldWorks 9, installed at C:\Program Files\SIL\FieldWorks 9\
(registry HKLM\SOFTWARE\SIL\FieldWorks\9)
**flexicon:** 4.8.0 (C:\Github\flexicon, flexicon/__init__.py version = 4.8.0)
**Date:** 2026-09-18
**Note on source-file locks:** no flexicon source file was edited. Only
scratch scripts under a temp scratchpad dir were written, plus these two
report files.

## Claim under test

Issue #321 asks whether two suspects in flexicon exhibit the #317 failure
class: a property that LOOKS like a live, mutable, backing collection
(Count/Add/Remove/Clear present) but is actually rebuilt fresh on
every access, so a mutation performed through one accessed handle is
invisible when the same logical collection is re-fetched.

- Suspect 1: WritingSystemOperations.py:495-501 -- does
  lp.VernacularWritingSystems / CurrentVernacularWritingSystems (and the
  Analysis equivalents) back a real, persistent store, or a derived list?
- Suspect 2: lcm_casting.py:791-823 clone_properties -- does the
  hasattr(attr_value, "Count") and hasattr(attr_value, "Add") duck-type
  predicate match any DERIVED (rebuilt-per-access) member on a live LCM
  object, and does any current caller reach one?

## Method

Three throwaway sandbox copies of the real "Sena 3" project were made with
shutil.copytree into tempfile.mkdtemp() directories, opened
write-enabled (undoable=False), exercised, and then the whole tempdir was
deleted with shutil.rmtree. The real Sena 3 project directory
(C:\ProgramData\SIL\FieldWorks\Projects\Sena 3) was never opened for
writing at any point in this session. Scripts used (all in a session-scoped
temp scratchpad dir, not checked into the repo):

- experiment.py -- Suspect 1 identity/mutation/fresh-refetch test on
  VernacularWritingSystems + CurrentVernacularWritingSystems, and
  Suspect 2's first predicate sweep on a live ILexEntry.
- experiment2.py -- Suspect 2 predicate sweep on a live IPhCode (one of
  the actual object types clone_properties is called on from
  PhonemeOperations.py); attempted (and failed to find) a populated
  IFsFeatStruc / PhContext sample in Sena 3's data.
- experiment3.py -- direct .Clear() probe on every UNKNOWN-SUFFIX
  predicate match found on ILexEntry, with a fresh re-fetch after each.
- experiment4.py -- control/contrast: same .Clear() probe on a genuine
  OS-suffixed collection (EtymologyOS), re-fetching the owning
  ILexEntry itself by Hvo from ServiceLocator (not just re-reading the
  attribute) to rule out any entry-level caching.

## Suspect 1 -- WritingSystemOperations VernacularWritingSystems /
CurrentVernacularWritingSystems

### Identity-per-access

    lp.VernacularWritingSystems is lp.VernacularWritingSystems -> False
    id(a1)= 2641884906896  id(a2)= 2641884907232
    lp.CurrentVernacularWritingSystems is lp.CurrentVernacularWritingSystems -> False

Identity-per-access is False -- by the naive heuristic in the task prompt
this LOOKS like the #317 shape (a new Python/COM wrapper object is
constructed on every property read). This alone is NOT sufficient
evidence of "derived" -- see the decisive test below.

### Baseline

    VernacularWritingSystems.Count = 2
    VernacularWritingSystems tags = [seh, seh-fonipa-x-etic]
    CurrentVernacularWritingSystems.Count = 2  tags = [seh, seh-fonipa-x-etic]
    DefaultVernacularWritingSystem = seh  Handle= 999000005
    Chosen non-default WS to test removal: seh-fonipa-x-etic  Handle= 999000006

### Mutation and fresh re-fetch (the decisive test)

    BEFORE remove: full_list.Contains= True  cur_list.Contains= True
    AFTER remove (SAME local handle): full_list.Contains= False  cur_list.Contains= False
    AFTER remove (FRESH re-fetch from lp): fresh_full.Contains= False  fresh_cur.Contains= False
    fresh_full.Count= 1  tags= [seh]
    fresh_cur.Count= 1  tags= [seh]

    VERDICT INPUT: fresh_full_contains_after_remove=False fresh_cur_contains_after_remove=False

The removal performed through the original handle is visible on a
brand-new property access (fresh_full = lp.VernacularWritingSystems,
freshly obtained, Contains() on it returns False, Count dropped from 2
to 1). This is the opposite of the #317 signature (where the stale local
handle appeared to change while a fresh re-fetch showed no change). The
wrapper object is rebuilt on each access (hence identity-per-access is
False), but it is rebuilt AS A VIEW ONTO the same live, persistent
IWritingSystemContainer backing store, not as an independent snapshot.

### Restore

    POST-RESTORE fresh_full.Contains= True  fresh_cur.Contains= True

Restored inside the sandbox before it was deleted (belt-and-suspenders; the
whole tempdir was discarded regardless).

## Suspect 2 -- clone_properties duck-type predicate

### Predicate sweep on a live ILexEntry (Sena 3 sandbox, Hvo=15,
1468 entries total in the sandbox)

    clone_properties predicate matches on ILexEntry (16):
    [AllSenses, AlternateFormsOS, DialectLabelsRS, DoNotPublishInRC,
     DoNotShowMainEntryInRC, EntryRefsOS, EtymologyOS,
     MainEntriesOrSensesRS, MinimalLexReferences, MorphTypes,
     MorphoSyntaxAnalysesOC, PronunciationsOS, PublishIn,
     ReferringObjects, SensesOS, ShowMainEntryIn]

      AllSenses:               UNKNOWN-SUFFIX  Count=9  identity(v1 is v2)=False
      AlternateFormsOS:        OWNED           Count=19 identity(v1 is v2)=False
      DialectLabelsRS:         REFERENCE       Count=0  identity(v1 is v2)=False
      DoNotPublishInRC:        REFERENCE       Count=0  identity(v1 is v2)=False
      DoNotShowMainEntryInRC:  REFERENCE       Count=0  identity(v1 is v2)=False
      EntryRefsOS:             OWNED           Count=0  identity(v1 is v2)=False
      EtymologyOS:             OWNED           Count=3  identity(v1 is v2)=False
      MainEntriesOrSensesRS:   REFERENCE       Count=0  identity(v1 is v2)=False
      MinimalLexReferences:    UNKNOWN-SUFFIX  Count=0  identity(v1 is v2)=False
      MorphTypes:              UNKNOWN-SUFFIX  Count=1  identity(v1 is v2)=False
      MorphoSyntaxAnalysesOC:  OWNED           Count=1  identity(v1 is v2)=False
      PronunciationsOS:        OWNED           Count=3  identity(v1 is v2)=False
      PublishIn:               UNKNOWN-SUFFIX  Count=1  identity(v1 is v2)=False
      ReferringObjects:        UNKNOWN-SUFFIX  Count=0  identity(v1 is v2)=False
      SensesOS:                OWNED           Count=9  identity(v1 is v2)=False
      ShowMainEntryIn:         UNKNOWN-SUFFIX  Count=1  identity(v1 is v2)=False

Identity-per-access is False for every entry here, including the
unambiguously real OS/OC collections -- confirming (again) that
identity-per-access is not diagnostic on its own for this LCM/pythonnet
binding. A direct .Clear() plus fresh-refetch probe was required.

### Decisive .Clear() probe -- UNKNOWN-SUFFIX members (same entry, Hvo=15)

    Testing .Clear() on ReferringObjects
      Clear() SUCCEEDED (unexpected!) -- re-check Count now: 0
      Fresh re-fetch ReferringObjects.Count after attempted Clear = 0
    Testing .Clear() on AllSenses
      Clear() SUCCEEDED (unexpected!) -- re-check Count now: 9
      Fresh re-fetch AllSenses.Count after attempted Clear = 9
    Testing .Clear() on MorphTypes
      Clear() SUCCEEDED (unexpected!) -- re-check Count now: 1
      Fresh re-fetch MorphTypes.Count after attempted Clear = 1
    Testing .Clear() on PublishIn
      Clear() SUCCEEDED (unexpected!) -- re-check Count now: 0
      Fresh re-fetch PublishIn.Count after attempted Clear = 0
    Testing .Clear() on ShowMainEntryIn
      Clear() SUCCEEDED (unexpected!) -- re-check Count now: 0
      Fresh re-fetch ShowMainEntryIn.Count after attempted Clear = 0
    Testing .Clear() on MinimalLexReferences
      Clear() SUCCEEDED (unexpected!) -- re-check Count now: 0
      Fresh re-fetch MinimalLexReferences.Count after attempted Clear = 0

AllSenses.Count was 9 before the probe. .Clear() raised no exception
(it "succeeded"), yet AllSenses.Count is still 9 on a fresh re-fetch of
the SAME .Clear()'d handle, and also 9 on a brand-new attribute
access. .Clear() operated on a throwaway, rebuilt-per-access object and
had zero effect on any real backing state. This is the #317 signature,
demonstrated directly on the code path clone_properties actually
exercises (dest_collection.Clear() at lcm_casting.py:811).

### Control: contrast against a genuine OS collection (EtymologyOS)

    Target entry Hvo= 15  EtymologyOS.Count= 3  AlternateFormsOS.Count= 19
    EtymologyOS: before= 3  after Clear() same handle Count= 0
    EtymologyOS fresh re-fetch (new entry object by Hvo) Count= 0

Here the re-fetch was maximally strict -- not just a fresh attribute read,
but a brand-new ILexEntry object obtained from
ServiceLocator.GetObject(Hvo) (bypassing any possible entry-level cache
too). EtymologyOS.Count dropped from 3 to 0 and stayed 0. EtymologyOS
(and by the same OS/OC reasoning AlternateFormsOS, EntryRefsOS,
MorphoSyntaxAnalysesOC, PronunciationsOS, SensesOS) is a real, live,
persistent backing collection: mutating it mutates the LCM.

### Predicate sweep on a second live type actually touched by a real caller
(IPhCode, from PhonemeOperations.py:390-397)

    Found live IPhCode: ClassName= PhCode
    clone_properties predicate matches on PhCode (1): [ReferringObjects]
      ReferringObjects: suffix=UNKNOWN-SUFFIX Count=0 identity(v1 is v2)=False

IPhCode's only Count/Add match is ReferringObjects, the same derived,
universal-on-ICmObject backreference property already shown above to be a
Clear()-is-a-no-op member.

### Types not reachable in Sena 3's data (documented gap, not guessed)

IFsFeatStruc (cloned from IPhPhoneme.FeaturesOA in
PhonemeOperations.py:374-384) and IPhContext
(EnvironmentOperations.py:631-652) were the other two live types real
callers pass to clone_properties. Sena 3's sandbox data has no phoneme
with FeaturesOA populated and no environment with a defined left/right
context, so neither type could be reached and enumerated live in this
session. This is reported as a genuine gap, not filled in with a guess.
Recommendation: to close this gap, either populate a phoneme's FeaturesOA
and an environment's context in a scratch project and re-run the same
enumerate_matches() probe, or reason from the .NET interface definitions
directly (out of scope for a live-only verification pass).

## Grep-grounded caller inventory for clone_properties

    PhonologicalRuleOperations.py:1397-1399  (rule duplicate: source/duplicate,
                                               concrete rule types e.g. IPhRegularRule)
    PhonemeOperations.py:368-397             (source_features/new_features IFsFeatStruc;
                                               code/new_code IPhCode)
    EnvironmentOperations.py:631-652          (src_context/new_context IPhContext family)

No call site passes an ILexEntry, ILexSense, or any other object type shown
above to have an UNKNOWN-SUFFIX derived member in its predicate-match set.
The one type both reachable live AND a real caller's argument (IPhCode)
only exposed the harmless (because Count was already 0 and the property is
universally a no-op per the ILexEntry test above) ReferringObjects member.

## Recommended discriminator (from the live evidence)

Key on the LCM ownership-suffix naming convention rather than duck-typing:

- OS / OC / OA suffix -> real owned collection/atomic; safe to Clear()/Add()
  as clone_properties does today. Confirmed live: AlternateFormsOS,
  EntryRefsOS, EtymologyOS, MorphoSyntaxAnalysesOC, PronunciationsOS,
  SensesOS.
- RS / RC / RA suffix -> reference collection/atomic; NOT owned. Present in
  the predicate-match set (DialectLabelsRS, DoNotPublishInRC,
  DoNotShowMainEntryInRC, MainEntriesOrSensesRS) but not live-tested for
  Clear()/Add() safety in this session -- cloning a reference collection by
  Clear()+factory.Create()+Add() is semantically wrong regardless of
  liveness (it should share the reference, not manufacture new objects),
  so this discriminator would also fix a second, independent bug class
  the current duck-type check does not distinguish.
- No suffix (AllSenses, MinimalLexReferences, MorphTypes, PublishIn,
  ReferringObjects, ShowMainEntryIn) -> derived/computed, proven live to be
  a Clear()-is-a-no-op member. The discriminator should exclude these
  outright.

### Does the hardening change behaviour for any CURRENTLY-matched member?

For the three real call sites (PhonologicalRuleOperations,
PhonemeOperations, EnvironmentOperations), the objects passed
(rule types, IFsFeatStruc, IPhCode, IPhContext family) were not observed,
live, to expose any RS/RC/RA or no-suffix Count/Add match except IPhCode's
ReferringObjects, which is already a proven no-op today. Restricting the
predicate to OS/OC/OA would not change today's observed behaviour for any
matched member on the one type (IPhCode) checked live; it would only
change behaviour if IFsFeatStruc or IPhContext turn out (unverified in
this session, see gap above) to expose a matching RS/RC/RA or no-suffix
member -- in which case the hardening would SILENTLY NARROW today's
(already-broken, per the pattern already proven) no-op behaviour into an
explicit skip, which is strictly safer, not more restrictive in any
harmful sense.

## Cleanup and non-modification confirmation

- All four experiment scripts operated exclusively on shutil.copytree
  tempdir COPIES of Sena 3, each deleted with shutil.rmtree in a
  finally: block at the end of its run (confirmed by the printed
  cleanup-done line in every run's captured output above).
- The real Sena 3.fwdata at
  C:\ProgramData\SIL\FieldWorks\Projects\Sena 3\Sena 3.fwdata was opened
  once, briefly, in a lock-check only (open(path, "r+b") then immediately
  closed, no LCM/FLEx layer involved) before the sandbox experiments began,
  to confirm it was not held open by a running FieldWorks instance. No LCM
  session, transaction, or write ever touched it.
- Target was not used in this investigation (Sena 3 sufficed and was
  preferred per the task).
- The database was left unmodified.

## Result

- Suspect 1 (WritingSystemOperations.py:495-501): live evidence shows the
  removal survives a fresh re-fetch from lp. CORRECT-AS-IS.
- Suspect 2 (lcm_casting.py:791-823 clone_properties): the duck-type
  predicate matches derived, rebuilt-per-access members (AllSenses,
  MorphTypes, PublishIn, ShowMainEntryIn, MinimalLexReferences,
  ReferringObjects observed live) and .Clear()/.Add() against them is a
  proven no-op. No CURRENT caller is confirmed to reach one of the
  data-losing (non-empty) variants; the one derived member reachable via a
  real caller's argument type (IPhCode.ReferringObjects) was empty in this
  data and so is a wasted-cycles no-op rather than a data-losing one today.
  This is a latent, predicate-level #317-class bug, confirmed live, not
  (on current evidence) a currently-triggered data-loss bug.

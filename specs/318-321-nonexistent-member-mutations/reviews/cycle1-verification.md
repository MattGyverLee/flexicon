# Cycle 1 verification -- issue #321 (derived-list investigation)

**Evidence:** specs/318-321-nonexistent-member-mutations/evidence/live-321-derived-lists.md
**Live run:** yes -- three disposable tempdir COPIES of the real Sena 3
project were opened write-enabled, mutated, and destroyed; the real project
was never opened for writing.
**Project used:** Sena 3 (sandbox copies only)
**FieldWorks:** FieldWorks 9 (C:\Program Files\SIL\FieldWorks 9)
**flexicon:** 4.8.0

## Verdicts

### Suspect 1 -- WritingSystemOperations.py:495-501
### VERDICT: CORRECT-AS-IS

`lp.VernacularWritingSystems` and `lp.CurrentVernacularWritingSystems` are
rebuilt (non-identical) Python/pythonnet wrapper objects on every access
(identity-per-access is False), but a `.Remove()` performed through one
access is visible on a completely fresh subsequent access: Count dropped
from 2 to 1 and `Contains()` on the removed writing system returned False
on the fresh handle too. This is the opposite of the #317 signature. The
in-code comment's removal contract (remove from the full list, then the
current list) is correctly implemented against a genuinely live backing
store (`IWritingSystemContainer`). The identity-per-access heuristic
proposed in the task is not, by itself, diagnostic for this binding --
the mutation/fresh-refetch test is the one that actually settles it, and
it settles in favour of CORRECT-AS-IS.

### Suspect 2 -- lcm_casting.py:791-823 clone_properties
### VERDICT: SILENT-NO-OP (latent, not currently triggered)

The `hasattr(attr_value, "Count") and hasattr(attr_value, "Add")` predicate
matches at least six derived, rebuilt-per-access members observed live on
`ILexEntry` (`AllSenses`, `MorphTypes`, `PublishIn`, `ShowMainEntryIn`,
`MinimalLexReferences`, `ReferringObjects`) and the same universal
`ReferringObjects` member on `IPhCode`. A direct `.Clear()` probe on
`AllSenses` (Count=9) raised no exception yet left the property's Count at
9 on every subsequent fresh re-fetch -- proving `dest_collection.Clear()`
in `clone_properties` (lcm_casting.py:811) is a genuine no-op against these
members, exactly the #317 failure class, now demonstrated on the actual
code path rather than inferred from static shape. In contrast, a real
`OS`-suffixed collection (`EtymologyOS`) cleared correctly and stayed
cleared even when re-fetched via a brand-new `ILexEntry` object pulled from
`ServiceLocator` by Hvo -- confirming the OS/OC ownership suffix is a
reliable live discriminator where duck-typing is not.

Grepping the three real call sites (`PhonologicalRuleOperations.py:1397-1399`,
`PhonemeOperations.py:368-397`, `EnvironmentOperations.py:631-652`) shows
none of them pass `ILexEntry` or any other object type this session found
to expose a non-empty derived Count/Add match. The one type both reachable
live AND passed by a real caller (`IPhCode`, from `PhonemeOperations.py`)
only exposed `ReferringObjects`, which was empty (Count=0) in the tested
data, so calling `clone_properties` on it today wastes a Clear()+no-op
cycle but loses no data. `IFsFeatStruc` and `IPhContext` -- the other two
real-caller argument types -- could not be reached live because Sena 3's
sandbox data has no phoneme with `FeaturesOA` populated and no environment
with a defined context; this is an honest gap, not a guess (see the
evidence file's "Types not reachable" section for how to close it).

**Bottom line:** the predicate is confirmed, live, to be capable of a
#317-class silent no-op. No currently-triggered data loss was found in this
session because the one type checked live that a real caller actually
passes (`IPhCode`) only exposed an empty derived collection. This is
reported as `SILENT-NO-OP` at the mechanism level (proven live) with the
caveat that "currently exploited by a real caller today" remains
`INCONCLUSIVE` for `IFsFeatStruc` / `IPhContext` specifically, pending data
that populates those code paths.

## Recommended fix (grounded in the live evidence)

Replace the duck-type predicate with a discriminator on the LCM ownership
suffix (`OS`/`OC`/`OA` = owned, safe to clone in place; anything else
skipped). This would not change today's observed live behaviour for the
one real-caller argument type checked (`IPhCode` -- its only match,
`ReferringObjects`, is already confirmed to be a no-op, so skipping it
outright is behaviourally identical, just without the wasted Clear()
call). For `IFsFeatStruc` / `IPhContext`, whether the hardening narrows any
currently-working behaviour remains unverified -- flagged above as the one
open question a future session with populated feature-structure /
environment-context data should close.

## Database state

The real Sena 3 project (`C:\ProgramData\SIL\FieldWorks\Projects\Sena 3`)
was left unmodified. Every mutation in this investigation happened inside
a `shutil.copytree` tempdir copy that was deleted with `shutil.rmtree`
immediately after each script finished. Confirmed unmodified.

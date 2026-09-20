# pyflexicon 4.9.0

**Released 2026-09-19** | `pip install --upgrade pyflexicon`

One new surface -- `project.Parser` -- plus three read accessors and one
silent-failure repair. The parser surface is **read-only by construction**:
there is no operation on it that writes anything back to the project. No
signature was removed, and no default a caller passes explicitly changed
meaning.

---

## The headline: `project.Parser`, a read-only parser surface

`ParserOperations` lives in the new `flexicon/code/Parser/` package and is
also exported at the package top level:

```python
from flexicon import FLExProject, ParserOperations
```

Six public methods, and that is the **entire** surface:

| Method | Returns |
|---|---|
| `GetAvailability()` | `ParserAvailability(available, reason, version)` |
| `ParseWord(word)` | parse result for a single wordform |
| `ParseWordXml(word)` | the same parse as the component's XML |
| `TraceWordXml(word, analyses=None)` | trace XML, optionally restricted to given analyses |
| `Reload()` | discards the loaded grammar and rebuilds it |
| `IsUpToDate()` | whether the loaded grammar still matches the model |

Ask availability first, then parse. This surface never needs write access:

```python
from flexicon import FLExProject

project = FLExProject()
project.OpenProject("MyProject", writeEnabled=False)

status = project.Parser.GetAvailability()
if not status.available:
    print("Parser unavailable: %s" % status.reason)
else:
    print("Parser %s" % status.version)
    for analysis in project.Parser.ParseWord("rumah"):
        print(analysis)
```

`project.Parsers` is retained as a **deprecated alias** for `project.Parser`.

---

## Read-only by construction

This is the load-bearing property of the whole surface, so it is stated
plainly rather than left to be inferred.

**There is no operation that records, files, or otherwise writes a parse
result back to the project.** No transaction is opened. No write-enable
check is performed -- because there is nothing to guard. A parse reads the
model and hands back an answer; it leaves no trace in the data.

This is **not a convention that a future edit could quietly erode**. A
standing test asserts the public surface by **set equality** over the
declared method names, so adding a member -- of any kind, however
innocuous its verb -- fails that test. Extending this surface is therefore
a deliberate contract change, made in the open, rather than something that
can slip through as a passing edit.

Callers rest real safety claims on this. FlexToolsMCP in particular
presents parser operations as read-only to its users; that claim is only
as good as the set-equality assertion behind it. Treat the test as part of
the API.

---

## Availability degrades, it does not explode

`GetAvailability()` returns `ParserAvailability(available, reason,
version)` and **never raises -- on any machine, in any condition**. Every
way the check can go wrong is reported as `available=False` with a `reason`
string: the component missing, relocated, belonging to a different
FieldWorks installation, present but unreadable, or pythonnet failing to
load it.

Only *calling an operation* raises, and when it does it raises with that
same reason. So the unavailable path is discoverable before you commit to
it, and self-explaining if you do not.

The component is **loaded by use, never by import**. `import flexicon`
succeeds on a machine with no parser component at all, which is why this
release adds no new install-time requirement.

### What the check actually checks

Two checks, and **neither of them reads a version number**:

1. **Same-installation** -- directory equality between the component and
   the already-loaded data model.
2. **Member presence** -- every member the class calls is present on the
   type.

The detected version is **reported and never compared against a minimum**.
If the members the code needs are there, it works; a version string is
information for you, not a gate.

**Be clear about the limit of check 1.** It is *directory equality only*.
It catches the real and common failure -- two FieldWorks installations
accidentally mixed inside one process -- and nothing beyond that. It does
not verify provenance, and a file substituted in the right directory
passes it.

---

## CAPABILITIES: `"parser"` means the build, not the machine

`flexicon.CAPABILITIES` gains the token `"parser"`.

**The token means: this build implements the surface.**

**The token does not mean: a parser is reachable on the machine reading
it.** Reachability depends on a FieldWorks component that this package
neither installs nor requires. Two machines running the identical wheel
can disagree about whether a parse is possible, and both are correct.

Consumers must therefore **probe**, not infer:

```python
if "parser" in getattr(flexicon, "CAPABILITIES", frozenset()):
    status = project.Parser.GetAvailability()   # ask the machine
    if status.available:
        ...
```

Use the one-line `getattr(..., frozenset())` form: releases at or below
4.3.0 do not define `CAPABILITIES` at all.

Inferring reachability from the token is the one misreading that turns a
graceful degrade-with-a-reason into a crash. It is worth a comment at the
call site.

---

## Grammar lifetime

At most **one loaded grammar at a time**, for the project currently in
use. Switching projects releases the previous one.

Currency is **asked of the parser before every reuse** and never cached
locally, so a grammar the component considers stale is never silently
reused on the strength of a flag flexicon set earlier.

`Reload()` is **reset-then-update -- two steps, deliberately**. The
component's bare update short-circuits when it believes nothing has
changed, so a one-step reload would return having done nothing, and the
next parse would be served from the very grammar the caller asked to
discard -- with no error and no way to tell. The reset makes the discard
unconditional. Verified live.

---

## New read accessors

None of these need a parser component.

- **`project.Texts.GetGenres(text)`** -- every genre on a text, and an
  empty list when it has none. The singular `GetGenre` is unchanged.
- **`project.Allomorphs.GetOwningEntry(allomorph_or_hvo)`** -- the owning
  `ILexEntry`, or `None`.
- **`project.MSA.GetAll(entry_or_hvo=None)`** -- an `MSACollection` of
  `MorphosyntaxAnalysis` wrappers. No `ClassName` dispatch and no casts
  for the caller.

---

## Fixed: an unrestricted trace silently poisoned later parses

`TraceWordXml()` with no analyses passed an **empty** restriction to the
component where it should have passed a **null**. The component treats
those as near-opposites: null means *no restriction*, empty means *admit
nothing*.

Two properties made that much worse than a single wrong answer. The
setting **outlives the call**, and a plain parse **never resets it**. So a
word that had parsed with one analysis returned zero analyses afterwards
-- indefinitely, for the life of the process, with no error anywhere.

Three changes close it:

- `None` now passes a genuine null.
- An **empty sequence is refused** with `FP_ParameterError` rather than
  being quietly widened into "no restriction". The two requests are
  different; guessing which one the caller meant is how this defect
  started.
- A real restriction is **cleared before the next plain parse**.

Found by live verification. The offline suite and all four structural
ratchets were green throughout -- worth noting, because it is a fair
description of what an offline suite can and cannot see.

---

## Verification

| Gate | Result |
|---|---|
| Offline suite (`-m "not requires_live_project"`) | **1923 passed, 826 deselected, 0 failed** |
| Live, read-only, `IndonesianHC-Complete` and `Malay Parsing-20230810withHC` | **18 passed, 0 skipped**, confirmed genuinely live |

Both live projects are HermitCrab-configured.

**Not verified live:** the automatic reload path firing when the model
changes underneath a held grammar. Exercising it requires a write, so it
is deferred to a later checkpoint. `Reload()`'s unconditional discard
*was* witnessed live; it is only the *automatic* trigger that is
unproven.

**Scope of the live evidence:** HermitCrab only. An XAmple-configured
project drives a different component and is not covered by these runs.

---

## Full detail

`CHANGELOG.md`, section `[4.9.0]`. Every entry carries its root-cause
analysis and the measurement that justified it.

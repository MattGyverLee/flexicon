# Exception Handling Guide for flexicon

## Overview

This guide documents proper exception handling in flexicon, which wraps FLEx's .NET LibLCM library in Python. Exception handling requires understanding both Python and .NET exception types, as FLEx operations throw .NET exceptions that must be caught explicitly.

**Key Principle:** flexicon is a bridge between Python and .NET. Always catch the actual .NET exception types that FLEx throws, not generic Python exception types.

---

## Exception Hierarchy

### Custom flexicon Exceptions

flexicon defines custom exception classes for API consistency and error context:

#### Project-Level Exceptions (FP_ProjectError)
These are raised during project opening and initialization:

- **`FP_ProjectError`** - Base exception for all project-related errors
- **`FP_FileNotFoundError`** - Project file does not exist or path is invalid
- **`FP_FileLockedError`** - Project is locked by another FLEx instance
- **`FP_MigrationRequired`** - Project needs migration in FLEx first

#### Runtime Exceptions (FP_RuntimeError)
These are raised during normal operation:

- **`FP_RuntimeError`** - Base exception for runtime errors
- **`FP_ReadOnlyError`** - Attempted write operation on read-only project
- **`FP_WritingSystemError`** - Invalid writing system for the project
- **`FP_NullParameterError`** - Required parameter is None
- **`FP_ParameterError`** - Invalid parameter value or type
- **`FP_TransactionError`** - Invalid transaction state, e.g. `AbortSession()` called inside a transaction block
- **`FP_ConflictingSaveError`** - Another client saved changes to the project that cannot be reconciled with this session's unsaved changes; raised by `flexicon.code.headless_ui.HeadlessLcmUI.ConflictingSave()` (see issue #238)

### .NET Exception Types to Catch

When working with FLEx operations, you'll encounter these .NET exceptions from LibLCM:

| Exception Type | Cause | Example |
|---|---|---|
| `System.Collections.Generic.KeyNotFoundException` | Object not found by HVO or GUID | Invalid object lookup |
| `System.FormatException` | Date/time or format parsing failed | `DateTime.Parse()` with invalid string |
| `System.InvalidCastException` | Type cast failed (e.g., to ILexEntry) | Invalid object type conversion |
| `System.ArgumentException` | Invalid argument to method | Wrong parameter value |
| `System.InvalidOperationException` | Operation not valid in current state | Add to read-only collection |
| `System.NullReferenceException` | Accessed null property/reference | Accessing non-existent object property |
| `System.IO.FileNotFoundException` | File not found | Missing project file |
| `System.IO.IOException` | I/O error | File access permission denied |
| `System.IndexOutOfRangeException` | Array/collection index out of bounds | Invalid sequence index |
| `LcmFileLockedException` | Project file is locked | Another FLEx instance has lock |
| `LcmDataMigrationForbiddenException` | Data migration required | Project schema too old |

Note that `System.InvalidOperationException` is also the exception the SLDR uses to report both "already initialized" and "not initialized" -- see "Library Initialization and the SLDR Lifecycle" below, where matching its message rather than probing state was the root cause of issue #249.

---

## Common Exception Patterns

### 1. Type Casting Exceptions

When converting LCM objects between types, several exceptions can occur:

**Pattern: Safe Casting with Type Checking**
```python
from flexicon import FLExProject, FP_ParameterError
import System

def safe_cast_to_person(obj):
    """
    Safely cast object to ICmPerson with proper exception handling.

    Raises:
        FP_ParameterError: If object cannot be cast to ICmPerson
    """
    try:
        # Attempt the cast
        person = ICmPerson(obj)
        return person
    except (TypeError, System.InvalidCastException) as e:
        # TypeError: Python-side type error
        # InvalidCastException: .NET-side cast error
        raise FP_ParameterError(f"Object is not a valid person: {e}")
    except System.NullReferenceException as e:
        # Object is null
        raise FP_ParameterError(f"Cannot cast null object: {e}")
```

**Pattern: Multi-Type Casting**
```python
def get_as_entry_or_sense(obj):
    """
    Try to cast object as ILexEntry, fall back to ILexSense.

    Returns:
        ILexEntry or ILexSense

    Raises:
        FP_ParameterError: If object is neither entry nor sense
    """
    try:
        return ILexEntry(obj)
    except System.InvalidCastException:
        try:
            return ILexSense(obj)
        except System.InvalidCastException as e:
            raise FP_ParameterError(
                f"Object is neither an entry nor a sense: {e}"
            )
```

---

### 2. Object Lookup Exceptions

When retrieving objects by HVO (Handle Value Objects) or GUID:

**Pattern: Safe Lookup with Specific Exception**
```python
from System.Collections.Generic import KeyNotFoundException

def get_object_by_hvo(project, hvo):
    """
    Retrieve an object by its HVO.

    Args:
        project: FLExProject instance
        hvo: Integer HVO value

    Returns:
        The requested object

    Raises:
        ValueError: If object not found
    """
    try:
        obj = project.Object(hvo)
        return obj
    except KeyNotFoundException as e:
        # Exception message format:
        # "Unable to find hvo XXXXX in the object dictionary"
        raise ValueError(f"Object HVO {hvo} not found: {e}")
```

**Pattern: Lookup with Logging**
```python
import logging

def find_entry_safe(project, entry_guid):
    """
    Find a lexical entry by GUID, with detailed logging.
    """
    logger = logging.getLogger(__name__)
    try:
        return project.LexiconGetEntry(entry_guid)
    except KeyNotFoundException as e:
        logger.error(f"Entry not found: {entry_guid}", exc_info=True)
        return None
```

---

### 3. Property Access Exceptions

Accessing object properties that may not exist or be null:

**Pattern: Safe Property Access**
```python
def get_lemma_form(entry):
    """
    Safely get the lemma form from a lexical entry.

    Returns:
        The form string, or None if not available
    """
    try:
        form_obj = entry.LexemeFormOA  # May be null
        if form_obj is None:
            return None
        form_string = form_obj.Form  # May be null
        if form_string is None:
            return None
        return form_string.Text
    except (AttributeError, System.NullReferenceException):
        # AttributeError: Python attribute doesn't exist
        # NullReferenceException: .NET null reference
        return None
```

**Pattern: Property Chain with Fallback**
```python
def get_entry_definition(entry):
    """
    Get the definition, with fallback strategies.
    """
    try:
        # Primary path: first sense definition
        sense = entry.SensesOS[0]
        definition = sense.Definition
        if definition and definition.Text:
            return definition.Text
    except (AttributeError, System.NullReferenceException, IndexError):
        pass  # Fall through to fallback

    try:
        # Fallback: entry-level definition
        return entry.Comment.Text
    except (AttributeError, System.NullReferenceException):
        pass

    return None  # No definition found
```

---

### 4. DateTime Parsing Exceptions

When parsing date/time values from strings:

**Pattern: Safe DateTime Parsing**
```python
from System import DateTime, FormatException

def parse_flex_date(date_string):
    """
    Parse a date string in FLEx format.

    Args:
        date_string: Date in string format

    Returns:
        System.DateTime object

    Raises:
        FP_ParameterError: If date string format is invalid
    """
    try:
        return DateTime.Parse(date_string)
    except FormatException as e:
        # Exception message format:
        # "The string was not recognized as a valid DateTime..."
        raise FP_ParameterError(
            f"Invalid date format '{date_string}': {e}"
        )
```

**Pattern: Date Validation with Type Checking**
```python
def safe_set_modification_date(object_item, date_string):
    """
    Safely set modification date with validation.
    """
    try:
        parsed_date = DateTime.Parse(date_string)
    except FormatException:
        # Log and use current date instead
        parsed_date = DateTime.Now

    try:
        object_item.ModifyDate = parsed_date
    except System.InvalidOperationException:
        # Object is read-only
        raise FP_ReadOnlyError()
```

---

### 5. Collection Operations Exceptions

When adding, removing, or modifying collection items:

**Pattern: Safe Collection Modification**
```python
from System import ArgumentException, InvalidOperationException

def add_sense_to_entry(entry, sense):
    """
    Safely add a sense to a lexical entry.

    Raises:
        FP_ParameterError: If sense cannot be added
        FP_ReadOnlyError: If entry is read-only
    """
    try:
        entry.SensesOS.Add(sense)
    except ArgumentException as e:
        # Sense already in collection or invalid type
        raise FP_ParameterError(f"Cannot add sense: {e}")
    except InvalidOperationException as e:
        # Likely read-only
        raise FP_ReadOnlyError()
```

**Pattern: Safe Collection Iteration**
```python
def get_valid_senses(entry):
    """
    Iterate senses with error handling.

    Returns:
        List of valid senses (skips problematic ones)
    """
    valid_senses = []
    try:
        for sense in entry.SensesOS:
            try:
                # Validate sense is usable
                if sense is not None:
                    valid_senses.append(sense)
            except (AttributeError, System.NullReferenceException):
                # Sense is corrupted or null, skip it
                continue
    except Exception as e:
        # Unexpected error iterating collection
        logging.error(f"Error iterating senses: {e}", exc_info=True)

    return valid_senses
```

---

### 6. Write Operation Exceptions

When attempting to modify project data:

**Pattern: Write With Permission Check**
```python
def update_entry_headword(project, entry, new_headword):
    """
    Update an entry's headword with write permission check.

    Raises:
        FP_ReadOnlyError: If project is read-only
        FP_ParameterError: If headword is invalid
    """
    if not project.WriteEnabled:
        raise FP_ReadOnlyError()

    try:
        form = entry.LexemeFormOA
        if form is None:
            raise FP_ParameterError("Entry has no lexeme form")

        # Create string for writing system
        ws_handle = project.WSHandle('en')
        mkstr = TsStringUtils.MakeString(new_headword, ws_handle)
        form.Form.set_String(ws_handle, mkstr)

    except (AttributeError, System.NullReferenceException) as e:
        raise FP_ParameterError(f"Cannot update headword: {e}")
```

---

## Migration Guide: Bare Except to Specific Exceptions

### Before (Bad Pattern)
```python
def process_entry(entry):
    """BAD: Uses bare except - catches everything including SystemExit!"""
    try:
        person = ICmPerson(entry)
        # ... process person ...
    except:  # WRONG! Catches all exceptions
        raise FP_ParameterError("Invalid entry")
```

**Problems with bare except:**
- Catches `SystemExit`, `KeyboardInterrupt` (can't exit properly)
- Catches `GeneratorExit` (breaks generator cleanup)
- Hides unexpected errors
- Makes debugging difficult
- Violates Python PEP 8 style guide

### After (Good Pattern)
```python
def process_entry(entry):
    """GOOD: Catches specific exception types."""
    try:
        person = ICmPerson(entry)
        # ... process person ...
    except (TypeError, System.InvalidCastException) as e:
        raise FP_ParameterError(f"Entry is not a person: {e}")
```

---

## Best Practices

### 1. Be Specific
Always catch the exact exception types you expect, not broad base classes.

**Bad:**
```python
try:
    obj = project.Object(hvo)
except Exception:  # Too broad
    pass
```

**Good:**
```python
try:
    obj = project.Object(hvo)
except KeyNotFoundException:  # Specific
    pass
```

### 2. Preserve Exception Context
Include the original exception in your error message or re-raise it.

**Bad:**
```python
except KeyNotFoundException:
    raise ValueError("Not found")  # Lost context
```

**Good:**
```python
except KeyNotFoundException as e:
    raise ValueError(f"Object not found: {e}")  # Context preserved
```

### 3. Re-raise When Appropriate
Don't silently swallow exceptions that indicate programming errors.

**Bad:**
```python
try:
    entry = ILexEntry(obj)
except System.InvalidCastException:
    pass  # Silently failed!
```

**Good:**
```python
try:
    entry = ILexEntry(obj)
except System.InvalidCastException as e:
    logger.error(f"Invalid cast: {e}")
    raise FP_ParameterError(f"Object is not an entry: {e}")
```

### 4. Log for Debugging
Use logging to capture exception details while still handling gracefully.

**Pattern: Log and Handle**
```python
import logging

logger = logging.getLogger(__name__)

def safe_operation(project):
    try:
        return project.DoSomething()
    except KeyNotFoundException as e:
        logger.debug(f"Object not found: {e}", exc_info=True)
        return None
    except System.InvalidOperationException as e:
        logger.error(f"Invalid state: {e}", exc_info=True)
        raise FP_ParameterError(f"Operation failed: {e}")
```

### 5. Test Error Paths
Write tests for exception handling to ensure errors are caught correctly.

**Pattern: Exception Testing**
```python
import pytest
from flexicon import FP_ParameterError

def test_invalid_cast_raises_error():
    """Test that invalid casts are caught and converted."""
    with pytest.raises(FP_ParameterError):
        agent = AgentOperations(project)
        agent.CreateHumanAgent("name", invalid_object)

def test_missing_object_returns_none():
    """Test that missing objects are handled gracefully."""
    result = find_entry_safe(project, "invalid-guid")
    assert result is None
```

### 6. Document Expected Exceptions
Always document what exceptions a function can raise.

**Pattern: Exception Documentation**
```python
def add_allomorph(entry, form_text):
    """
    Add a new allomorph to an entry.

    Args:
        entry: ILexEntry instance
        form_text: String form of the allomorph

    Returns:
        The new IMoForm object

    Raises:
        FP_ReadOnlyError: If project is read-only
        FP_ParameterError: If entry is null or form_text is empty
        System.InvalidCastException: If entry is not actually an ILexEntry
    """
    if not entry:
        raise FP_ParameterError("Entry cannot be null")
    # ... implementation ...
```

---

## Library Initialization and the SLDR Lifecycle

Initialization and teardown are the one place where the "catch specific
exceptions" rule above is not merely tidier -- it is the difference between a
loud startup failure and silent, self-perpetuating data damage. This section
states the rule and uses issue #249 as the worked example.

### Rule: probe published state, don't match an initializer's exception

If a library publishes a state probe, use it. Reach for `try`/`except` only
for the check-then-act race the probe cannot close, and narrow that `except`
to the one exception type *and* the one message that means "benign".

`SIL.WritingSystems.Sldr` publishes exactly such a probe. Verified by live
reflection against **SIL.WritingSystems 18.0.0.0 / FieldWorks 9.3.10**:

| Member | Type | Verified behaviour |
|---|---|---|
| `Sldr.IsInitialized` | `public static bool`, get-only | Safe to read before any init; never throws |
| `Sldr.Initialize(offlineTestMode)` | static; parameter optional, default `False` | A second call throws `System.InvalidOperationException` and never re-applies the offline-mode argument |
| `Sldr.Cleanup()` | static | Throws `System.InvalidOperationException` when the SLDR is cold (from the private `CheckInitialized()`) |
| `Sldr.OfflineMode` | **does not exist** | There is no such member; the parameter is named `offlineTestMode` |

The two exception messages are exact, and they are **not** symmetric, so a
substring match written for one will not fire for the other:

| Call | Condition | `e.Message` |
|---|---|---|
| `Sldr.Initialize(True)` | already initialized | `The SLDR has already been initialized.` |
| `Sldr.Cleanup()` | never initialized, or already cleaned up | `The SLDR has not been initialized.` |

`Cleanup()` followed by `Initialize(True)` is a **supported cycle**: it works,
and `Sldr.LanguageTags` repopulates afterwards (9596 entries). A long-running
consumer that opens and closes several projects in one process may therefore
cycle the SLDR legitimately.

### Why a bare `except Exception` around an initializer is uniquely dangerous

Elsewhere in this guide, swallowing an exception costs you one operation and
one confusing log line (see "Be Specific" and "Re-raise When Appropriate"
above). Around an **initializer** it costs the whole process, because the
library stays down and every later call degrades instead of failing.

Issue #249 is the worked example. `FLExInitialize()` contained:

```python
# WRONG -- the shape that shipped, and the reason #249 went unnoticed.
try:
    Sldr.Initialize(True)
except Exception:
    logger.warning("Sldr.Initialize failed (already initialized?)")
```

The chain that produces:

1. Initialization fails for a **real** reason. The `except` downgrades it to
   a WARNING on logger `flexicon.code.FLExInit`, and the message
   **misattributes** the cause as the benign already-initialized case.
2. The SLDR is now down for the lifetime of the process.
3. Every LDML read inside liblcm's
   `CoreLdmlInFolderWritingSystemRepository` throws *"The SLDR has not been
   initialized"*.
4. liblcm reads that as a malformed file: it renames the project's `.ldml`
   to `.ldml.bad`, writes a `badldml.log` entry, and re-synthesizes the
   writing systems from defaults.
5. The next open repeats steps 1-4. Observed live: a `WritingSystemStore`
   left with no valid `.ldml` at all, 16 quarantine events over 8
   consecutive opens (with a quarantine landing 9 seconds after FLEx itself
   wrote the file), ending in a liblcm modal *"Unable to create writing
   system: en"*.

Actual data loss was negligible -- only default content was ever
overwritten -- but the cycle never terminates, and the *only* diagnostic it
ever emitted pointed at the wrong cause. That is the real cost of the bare
`except`: not the lost exception, but the plausible-looking log line that
stopped anyone looking further.

### Trap: pythonnet loses the exception type on CLR **property** getters

Do not detect initialization state by reading a property and catching what
comes out. Reading `Sldr.LanguageTags` before init surfaces as a bare:

```
TypeError: Exception has been thrown by the target of an invocation.
```

The inner `System.InvalidOperationException` -- and the message naming the
cause -- is **lost**. Only **method** calls are reliably exception-typed
across the pythonnet boundary; **CLR property getters** are not.

```python
# WRONG -- this except never matches; you get a bare TypeError instead.
try:
    tags = Sldr.LanguageTags
except System.InvalidOperationException:
    Sldr.Initialize(True)

# GOOD -- probe the documented state instead.
if not Sldr.IsInitialized:
    Sldr.Initialize(True)
```

A corollary for the rest of this guide: a `TypeError` raised out of a CLR
property access is not necessarily a Python-side type error. It may be any
.NET exception at all, with its identity stripped.

### The correct code shape

```python
import System
from SIL.WritingSystems import Sldr

logger = logging.getLogger(__name__)

def FLExInitialize():
    if Sldr.IsInitialized:
        logger.debug("Sldr already initialized; skipping Sldr.Initialize()")
    else:
        try:
            Sldr.Initialize(True)          # offlineTestMode=True
        except System.InvalidOperationException as e:
            # Backstop for the check-then-act race ONLY: Initialize() and
            # Cleanup() serialize on a private lock, so another thread can
            # win between the probe and the call. Anything that is not that
            # exact benign message is a real failure and must propagate.
            if "already been initialized" not in e.Message:
                raise
            logger.debug("Sldr was initialized concurrently; continuing")

def FLExCleanup():
    # Teardown must tolerate already being done: Sldr.Cleanup() throws when
    # the SLDR is cold, so an unguarded call made FLExCleanup() raise
    # whenever FLExInitialize() had never run or cleanup ran twice (several
    # shipped scripts under examples/ call it twice by design).
    if not Sldr.IsInitialized:
        logger.debug("Sldr not initialized; skipping Sldr.Cleanup()")
        return
    Sldr.Cleanup()
```

Three properties are worth naming explicitly:

- **Every genuine failure now propagates to the caller.** A broken SLDR is a
  startup error, not a warning.
- **The benign path no longer raises at all**, so repeated `FLExInitialize()`
  calls stay a genuine no-op -- which the shipped examples and per-test
  `setUp` rely on.
- **Teardown is idempotent**, in both directions.

As implemented in `flexicon/code/FLExInit.py`.

### `.ldml.bad` does not identify which half of the lifecycle broke

Issue #179 (*"WritingSystemOperations.Create leaves orphan tags; SLDR
teardown in unit tests marks .ldml files as bad"*, RESOLVED, commit
e42da05) produced the **same** `.ldml.bad` symptom from the **opposite**
cause: the SLDR was torn down mid-session by test teardown, rather than
never having come up. It changed zero lines of `FLExInit.py`, and it is not
a duplicate of #249.

When you see `.ldml.bad`, check both halves: whether `Sldr.IsInitialized` is
`False` at the time of the LDML read, and whether anything called
`Sldr.Cleanup()` earlier in the process.

See `docs/API_ISSUES_CATEGORIZED.md` "Category 12: Library-initialization /
SLDR lifecycle traps (issue #249)" for the full member table, the
anti-pattern list, and the #179/#249 comparison.

---

## Atomicity Under `undoable=False`: the Session Is the Unit

**This section states the actual, verified atomicity guarantee for the
legacy opt-out write mode (`undoable=False`). Since 4.4.0 the default is
`undoable=True` (task DEF) and the section below it applies instead; you
reach this mode only by passing `undoable=False` explicitly. Read this
before relying on `Transaction()` or `_TransactionCM` for rollback.**

`OpenProject(..., writeEnabled=True, undoable=False)`
opens exactly one LCM `NonUndoableUnitOfWork` for the entire session
(`BeginNonUndoableTask()` at open, `EndNonUndoableTask()` at close). There is
no per-operation or per-`Transaction()` rollback boundary inside that
envelope, because the LCM API a rollback would need --
`RollbackToMark` -- **does not exist** anywhere in liblcm or FieldWorks
(issue #236, confirmed by reflection over `SIL.LCModel.dll`; see
`specs/write-path-transactions/spec.md` section 2 and decision D1).

**Consequence:** the atomicity unit in this mode is the **session**, not the
operation and not the `Transaction()`/`_TransactionCM` block. If any code
raises partway through a multi-step write -- whether inside a
`with project.Transaction(...)` block, inside a `_TransactionCM`-wrapped
Operations method, or between unrelated calls -- every mutation applied
**before** that point remains in the in-memory LCM cache. Nothing is undone.
Those mutations will be written to disk on the next `SaveChanges()` or
`CloseProject()` call, exception or no exception.

```python
project.OpenProject("MyProject", writeEnabled=True, undoable=False)  # explicit opt-out

with project.Transaction("import batch"):
    project.LexEntry.Create("run", "stem")     # (1) applied
    project.LexEntry.Create("walk", "stem")    # (2) applied
    raise RuntimeError("network timeout mid-import")
    # (1) and (2) are NOT rolled back. They are still in the cache.

project.CloseProject()  # (1) and (2) are saved to disk, despite the exception.
```

**What this means for callers:**
- Design write operations to be safely re-runnable, or checkpoint before a
  risky batch so a failure is recoverable by inspection rather than by
  rollback.
- Do not treat a caught exception from inside a `Transaction()` block as
  evidence that no partial state was written -- assume the opposite.
- A single warning to this effect is logged once, at `OpenProject()` time
  (not once per transaction, which would train callers to ignore it).
- `FLExProject.RefreshFromDisk()` and `FLExProject.AbortSession()` operate at
  session granularity for the same reason: there is no finer granularity
  available in `undoable=False`.
- **`AbortSession()` is the recovery tool for exactly the situation above.**
  It calls liblcm's one real revert primitive, `IActionHandler.Rollback(0)`,
  discarding everything the session has written but not yet committed -- so
  in the example, calling it in the `except` block really does remove (1) and
  (2). It then reopens the session envelope, so the abort is non-terminal and
  the session stays usable. What it cannot revert is anything already on disk
  when the session opened.
- **Do not call `SaveChanges()` in this mode.** It cannot succeed: the
  session envelope holds the FSM in `ProcessingDataChanges`, while
  `SaveInternal()` requires `ReadyForBeginTask`. It raises a raw
  `System.InvalidOperationException("Commit at wrong place.")` *and* rolls
  back the open bundle on the way out, discarding uncommitted work.
  `CloseProject()` is the supported way to persist, and is unaffected (it
  ends the envelope before saving).
- If you need real per-operation rollback, simply **stop passing
  `undoable=False`** -- `undoable=True` is the default since 4.4.0 and is the
  destination mode decision D3 designates. The Track B rewrite of
  `flexicon/code/transaction.py` onto liblcm's `UndoableUnitOfWorkHelper` has
  landed, so an exception inside a block genuinely rolls that block back. See
  `specs/write-path-transactions/spec.md` D2/D3/B1. Note `AbortSession()`
  deliberately refuses in that mode (per-operation rollback is already
  automatic there); see tasks.md D8.

---

## Atomicity Under `undoable=True` (the default): the Block Is the Unit

This is the mode `undoable=False`'s caveats point at, the destination
decision D3 designates, and **since 4.4.0 the default** -- it is what you get
from a plain `OpenProject(..., writeEnabled=True)` (task DEF). Everything
below is verified against a live LCM in
`tests/operations/test_undoable_mode_live.py`; see
`specs/write-path-transactions/evidence/live-def-undoable-coverage.md`.

**The guarantee:** an exception inside a `with project.UndoableOperation(...)`
block rolls that block's mutations back, for real, via liblcm's
`UndoableUnitOfWorkHelper`. Creates, field writes and deletes are all
reverted, and the rollback is durable -- a rolled-back object does not
reappear when the project is reopened.

```python
project.OpenProject("MyProject", writeEnabled=True)   # undoable=True (default)

with project.UndoableOperation("import batch"):
    project.LexEntry.Create("run", "stem")     # (1)
    project.LexEntry.Create("walk", "stem")    # (2)
    raise RuntimeError("network timeout mid-import")
    # (1) and (2) ARE rolled back. Neither reaches disk.
```

**Every operation is its own unit of work.** A bare Operations call with no
block around it opens, commits and closes its own `UnitOfWork` -- that is the
`per-operation-uow` capability, and it holds end to end (the write survives
`CloseProject()`). Each such call is one entry in the FLEx Ctrl+Z menu,
labelled from the call's own arguments (`Create part of speech 'Noun'`), not
from the method name.

**A rejected input costs nothing.** Validation runs outside the bracket, so a
call that raises `FP_ParameterError` adds no undo entry and opens no unit of
work. Callers get no empty entries on a linguist's undo stack.

### Nesting joins -- an inner block has no independent rollback

Nested blocks **join** the enclosing unit of work rather than opening a second
one. This is not a style choice: liblcm's `UndoStack` responds to a second
`BeginUndoTask` by rolling the *already-open* unit back and then throwing, so
joining is what keeps an inner block from destroying the outer block's work.

The consequence callers must know:

```python
with project.UndoableOperation("outer"):
    try:
        with project.UndoableOperation("inner"):
            project.LexEntry.Create("partial", "stem")
            raise RuntimeError("boom")
    except RuntimeError:
        pass          # <-- swallowing the inner exception here
# "partial" IS COMMITTED. The inner block joined the outer unit of work,
# so it had no rollback of its own; only the OUTERMOST block's exit decides.
```

If you need the inner step to be independently revertible, it must not be
nested -- run it as its own top-level block, or let the exception propagate
out of the outer block so the whole unit rolls back together.

### Other mode-specific behaviors

- **`AbortSession()` refuses inside a block** (`FP_TransactionError`) and
  returns `False` between operations. It is in practice an `undoable=False`
  primitive; per-operation rollback already covers this mode. See tasks.md D8.
- **`Undo()`/`Redo()` are in-process only** (issue #235). They drive the live
  `ActionHandlerAccessor`, whose stack lives in RAM and is never serialized
  into `.fwdata`. A reopened project always starts with `CanUndo()` False, so
  work committed by a previous session is past undoing.
- **Never write `helper.RollBack = ...`.** `RollBack` is `{private get; set;}`
  and pythonnet synthesizes no property for it, so the assignment silently
  lands on the Python wrapper and leaves the real field at its default of
  `True` -- rolling back every clean unit of work. Use `set_RollBack(...)`.
  This is decision D9, and it is why a pythonnet write must always be verified
  by reading the effect back through the LCM.

---

## Testing Exception Handlers

### Unit Testing Pattern
```python
class TestExceptionHandling(unittest.TestCase):

    def setUp(self):
        self.project = FLExProject()
        self.project.OpenProject("test_project", writeEnabled=True)

    def tearDown(self):
        self.project.CloseProject()

    def test_invalid_hvo_raises_value_error(self):
        """Test that invalid HVO lookup raises ValueError."""
        with self.assertRaises(ValueError):
            get_object_by_hvo(self.project, 999999999)

    def test_null_parameter_raises_fp_error(self):
        """Test that null parameter is caught."""
        with self.assertRaises(FP_ParameterError):
            add_sense_to_entry(None, self.sense)

    def test_readonly_raises_fp_readonly_error(self):
        """Test that write to read-only project raises error."""
        self.project.CloseProject()
        self.project.OpenProject("test_project", writeEnabled=False)

        with self.assertRaises(FP_ReadOnlyError):
            update_entry_headword(self.project, self.entry, "new")
```

### Integration Testing Pattern
```python
def test_safe_entry_modification_workflow():
    """Test complete workflow with exception handling."""
    project = FLExProject()

    try:
        project.OpenProject("test_project", writeEnabled=True)

        # This should succeed
        entry = project.LexiconGetEntry("known-guid")
        entry_def = get_entry_definition(entry)

        # This should be caught and logged
        missing_entry = find_entry_safe(project, "unknown-guid")
        assert missing_entry is None

    except (FP_ProjectError, FP_FileNotFoundError) as e:
        pytest.skip(f"Project not available: {e}")
    finally:
        project.CloseProject()
```

---

## Import Reference

### Import flexicon Exceptions
```python
from flexicon import (
    FP_ProjectError,
    FP_FileNotFoundError,
    FP_FileLockedError,
    FP_MigrationRequired,
    FP_RuntimeError,
    FP_ReadOnlyError,
    FP_WritingSystemError,
    FP_NullParameterError,
    FP_ParameterError,
    FP_TransactionError,
    FP_ConflictingSaveError,
)
```

### Import .NET Exceptions
```python
import System
from System.Collections.Generic import KeyNotFoundException
from System import (
    InvalidCastException,
    FormatException,
    ArgumentException,
    InvalidOperationException,
    NullReferenceException,
    IndexOutOfRangeException,
)
from System.IO import (
    FileNotFoundException,
    IOException,
)
from SIL.LCModel import (
    LcmFileLockedException,
    LcmDataMigrationForbiddenException,
    LcmInvalidClassException,
    LcmInvalidFieldException,
)
```

---

## Exception Handling Checklist

When implementing exception handling in flexicon:

- [ ] Identify what .NET exceptions the operation can throw
- [ ] Catch specific exception types, not generic `Exception`
- [ ] Convert .NET exceptions to flexicon custom exceptions where appropriate
- [ ] Include original exception in error messages
- [ ] Log exceptions for debugging (use `logger.debug()` with `exc_info=True`)
- [ ] Document expected exceptions in docstrings
- [ ] Write tests for exception paths
- [ ] Test both success and failure cases
- [ ] Avoid silently swallowing important exceptions
- [ ] Consider whether to re-raise or handle locally
- [ ] For an initializer or a teardown, probe the library's published state (e.g. `Sldr.IsInitialized`) instead of matching an exception message, and never wrap it in a bare `except Exception`

---

## See Also

- **Phase 0 Verification Report:** `tests/PHASE_0_VERIFICATION_REPORT.md`
  - Documents actual exception types thrown by FLEx
  - Lists specific exception messages and contexts

- **Phase 0 Action Items:** `tests/PHASE_0_ACTION_ITEMS.md`
  - Lists required exception handling changes
  - Shows before/after examples

- **API Surface Documentation:** `docs/API_SURFACE.md`
  - Documents available operations and their parameters

- **Linguistic Safety Guide:** `docs/LINGUISTIC_SAFETY_GUIDE.md`
  - Best practices for linguistic data operations

---

## Troubleshooting

### "Exception was unhandled: KeyNotFoundException"
**Cause:** Trying to access an object with invalid HVO
**Fix:** Wrap lookup in try/except for `KeyNotFoundException`

```python
try:
    obj = project.Object(hvo)
except KeyNotFoundException:
    # Handle missing object
    pass
```

### "FormatException: String not recognized as valid DateTime"
**Cause:** DateTime string format is wrong
**Fix:** Validate format before parsing or catch `FormatException`

```python
try:
    dt = DateTime.Parse(date_string)
except FormatException:
    # Use ISO format or prompt user for correct format
    dt = DateTime.Parse("2026-02-21")
```

### "Project is read-only" during writes
**Cause:** Project opened without `writeEnabled=True`
**Fix:** Check write permission before attempting modifications

```python
if not project.WriteEnabled:
    raise FP_ReadOnlyError()
```

### "Object is not a valid entry" with InvalidCastException
**Cause:** Trying to cast wrong object type
**Fix:** Check object type before casting

```python
try:
    entry = ILexEntry(obj)
except System.InvalidCastException:
    # Verify object type or use different cast
    sense = ILexSense(obj)
```

---

**Document Version:** 1.0
**Last Updated:** 2026-02-21
**Author:** flexicon Development Team

# Issue draft (NOT YET FILED)

Filed by: nobody yet. Opening GitHub issues is a user-authorized action, so
this is staged as a ready-to-run draft rather than filed by the crew.

To file:

```powershell
gh issue create --repo MattGyverLee/flexicon `
  --title "ReversalIndexOperations.Create stores an int WS handle as a stringified int, breaking every downstream WritingSystem consumer" `
  --body-file specs/236-guid-create-agent-reversals/issues/reversal-index-writingsystem-int-handle.md
```

(Strip this header block before filing, or paste the body below by hand.)

---

## Summary

`ReversalIndexOperations.Create()` assigns `IReversalIndex.WritingSystem`
with an unconditional `str()`:

```python
# flexicon/code/Reversal/ReversalIndexOperations.py:191
new_index.WritingSystem = str(writing_system)
```

`WritingSystem` on `IReversalIndex` is a Unicode property holding an **ICU
locale tag** (`"en"`, `"pt-BR"`). But `Create()`'s own docstring shows callers
passing an int writing-system *handle*. When they do, `str(handle)` stores the
stringified integer -- e.g. `"999000001"` -- into a field that every consumer
reads back as a locale tag.

Discovered incidentally while writing the live test suite for the `guid=`
work on `Agents`/`ReversalIndexes`/`ReversalEntries` (see
`specs/236-guid-create-agent-reversals/`). It is **pre-existing and
independent** of that change, which is why it was sidestepped there rather
than fixed in-scope.

## Impact

`ReversalIndexEntryOperations` resolves an entry's writing system from the
owning index in three places:

- `ReversalIndexEntryOperations.py:202` (`Create`)
- `ReversalIndexEntryOperations.py:306`
- `ReversalIndexEntryOperations.py:656`

each doing `ws_str = index.WritingSystem` and then `self.project.WSHandle(ws_str)`.
Given a stringified int, `WSHandle()` cannot resolve it, returns nothing, and
the failure surfaces far from its cause as an `ArgumentNullException` raised
deep inside `TsStringUtils.MakeString`. So: **create an index by handle, then
create any entry in it, and entry creation blows up with an unrelated-looking
.NET exception.**

`FindByWritingSystem()` (`:326`, comparing `idx.WritingSystem == ws_str`) and
`GetWritingSystem()` (`:431`) are affected the same way -- an index created by
handle is not findable by its locale tag.

## Reproduction

```python
ws = <an int analysis WS handle>
idx = project.ReversalIndexes.Create("scratch", ws)
project.ReversalIndexes.GetWritingSystem(idx)   # -> "999000001", not "en"
project.ReversalEntries.Create(idx, "run")      # -> ArgumentNullException in MakeString
```

Workaround in the meantime: pass `wsHandle=` explicitly to
`ReversalEntries.Create()` so it never falls back to reading the index's own
`WritingSystem`. That is what
`tests/operations/test_guid_create_agent_reversals_live.py` does (see the
`_make_index` docstring), and it is a legitimate supported parameter -- but it
only papers over the entry path, not `FindByWritingSystem` / `GetWritingSystem`.

## Suggested direction

Normalize at the boundary in `Create()`: if `writing_system` is an int (or an
int-valued string), convert the handle to its ICU locale tag before assigning
-- there is already a handle->tag path available via the project's writing
system services -- and only `str()` a value that is already a tag. Then decide
whether `FindByWritingSystem()` should accept both forms symmetrically (it
currently stringifies its argument the same way, so handle-in/handle-stored
happens to round-trip, which is exactly what hides the bug from that method's
own tests).

Live verification against the Target project is required for the fix: create
an index by handle, read `WritingSystem` back from the LCM, and create an
entry in it without passing `wsHandle=`.

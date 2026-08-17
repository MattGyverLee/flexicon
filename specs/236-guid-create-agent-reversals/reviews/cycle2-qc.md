# Cycle 2 - QC review of the guid= implementation

Note: produced by lex-author (standing in for lex-qc, which is not an
available Agent type) in read-only mode; the main session persisted it
verbatim to this path.

Score: 96/100

## P0 (blocks merge)

None found.

## P1 (should fix before merge)

None found.

## P2 (nice-to-have, non-blocking)

- `flexicon\code\Reversal\ReversalIndexEntryOperations.py:277-291` -- the
  `_make_index` test helper documents a pre-existing bug (int WS handle stored
  as a stringified int in `IReversalIndex.WritingSystem`, breaking
  `ReversalIndexEntryOperations.Create`'s own WS-resolution fallback)
  discovered incidentally while writing this test. It is correctly called out
  of scope and sidestepped via explicit `wsHandle=`, but it is currently only
  documented in a test docstring -- worth filing as its own tracked issue so it
  is not lost.
- No test exercises `_CreateWithGuid`'s malformed-guid path opening zero
  transactions (i.e. asserting `FP_ParameterError` is raised *before* any DB
  write) -- implicit from `_CreateWithGuid`'s own docstring/precedent, but an
  explicit assertion (e.g. re-reading the `GetAll()` count unchanged) would
  close the loop for these three call sites specifically.

## Verified against the cycle-1 spec

- **Signatures**: `AgentOperations.Create(name, wsHandle=None, guid=None)`,
  `ReversalIndexOperations.Create(name, writing_system, guid=None)`,
  `ReversalIndexEntryOperations.Create(index_or_hvo, form, sense=None,
  wsHandle=None, guid=None)` -- all trailing positional-with-default, no
  reordering, matching all 8 `_CreateWithGuid` precedents
  (`WordformOperations.Create` lines 129-179).
- **Docstrings**: all three contract points from cycle 1 landed verbatim --
  (a) `ReversalIndexOperations.py:153-157` duplicate-WS still raises with a
  guid supplied, (b) `ReversalIndexEntryOperations.py:147-151` guid documented
  transport-only / zero-dedup, (c) `AgentOperations.py:133-137` bootstrap-GUID
  (`kguidAgentDefUser` etc.) fallback note.
- **Validate-then-mutate**: `ReversalIndexOperations.py:178-180` -- the
  duplicate-WS `FindByWritingSystem`/`FP_ParameterError` check runs
  unconditionally before `_TransactionCM`/`_CreateWithGuid`, not weakened and
  not gated on guid.
- **Transactions**: all three nest `_CreateWithGuid`'s inner `_TransactionCM`
  inside an outer `_TransactionCM`, identically to Wordform
  (`AgentOperations.py:172-181`, `ReversalIndexOperations.py:182-198`,
  `ReversalIndexEntryOperations.py:205-221`) -- no dropped, doubled, or
  unclosed transaction.
- **Out of scope untouched**: `AgentOperations.Duplicate()` (lines 210-253) is
  unchanged -- still unconditional `factory.Create()`, no guid param, as
  specified.
- **Test file**: GUID assertions re-query via `project.Object(guid_str)` ->
  `ServiceLocator.GetObject` (`FLExProject.py:3212-3226`), not the passed-in
  handle. Duplicate-GUID fallback covered for all three classes.
  `pytestmark = pytest.mark.requires_live_project` applied at module scope,
  covering every test. Uses `target_sandbox` (tempdir copy), never the live
  Target directly.
- **No emojis** anywhere in the four changed files (checked by pattern).

## Files reviewed

- `flexicon\code\Lists\AgentOperations.py`
- `flexicon\code\Reversal\ReversalIndexOperations.py`
- `flexicon\code\Reversal\ReversalIndexEntryOperations.py`
- `tests\operations\test_guid_create_agent_reversals_live.py`
- `flexicon\code\BaseOperations.py` (`_CreateWithGuid`, 1884-1962) and
  `flexicon\code\TextsWords\WordformOperations.py` (129-179) as the precedent
  baseline.

Reviewed By: lex-author (QC role), cycle 2

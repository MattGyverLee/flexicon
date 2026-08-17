# Cycle 3 programmer B2g: unbracketed-mutation ratchet guard

**Task:** B2g (specs/write-path-transactions/tasks.md) -- make decision D5
(per-site `with self._TransactionCM(...)` bracketing of all mutators)
mechanically enforceable via CI, independent of reviewer diligence across
294 hand edits spanning ~60 files.

**Scope discipline:** all work is under `tests/`. Nothing under
`flexicon/code/` was read-write; `transaction.py` and `FLExProject.py` were
not touched (another agent owns those concurrently). No commit was made.

## Files added

- `tests/write_path_transactions/__init__.py` -- empty, package marker.
- `tests/write_path_transactions/scan_unbracketed_mutations.py` -- the AST
  scanner. Importable (`from tests.write_path_transactions.scan_unbracketed_mutations
  import scan`) and runnable as a CLI (`python -m
  tests.write_path_transactions.scan_unbracketed_mutations [--json]
  [--baseline PATH]`).
- `tests/write_path_transactions/snapshots/unbracketed_baseline.json` --
  the frozen baseline artifact (295 entries; see Discrepancy below).
- `tests/write_path_transactions/test_unbracketed_mutations.py` -- the
  pytest ratchet, structured after `tests/contract/test_lcm_contract.py`'s
  baseline-comparison pattern (checked-in JSON snapshot + a pytest class
  that diffs live-computed state against it).

## Scanner method (mirrors cycle1-explore-b2sweep.md)

Walks every `.py` under `flexicon/code` (skipping `__pycache__` and
`*.backup`), and for every method directly in a class body, walks its
body tracking whether each node is lexically inside a
`with self._TransactionCM(...)` block. A method is "unbracketed" if it
contains at least one mutation-indicator node outside such a block.

Indicators implemented: `.Create(...)` (any receiver, including
`self.Create(...)` recursion -- labelled "factory.Create" per the cycle-1
table's own convention) plus a narrow extra match for
`<factory-ish-var>.Create<Suffix>(...)` to catch
`Scripture/ScrSectionOperations.py`'s `factory.CreateScrSection(...)`;
`.Delete`, `.Remove`, `.RemoveAt` (labelled `.Remove`), `.Add`, `.MoveTo`,
`.Replace`, `.Clear`, `.Insert`, `SetString`, `set_String`, `MergeObject`;
and assignment to any attribute ending in `RA`/`OA`/`OS`/`RS`.

Exclusions implemented:
- Pure delegation to a sibling Operations class's public method, narrowly
  matched as the exact shape `self.<CapitalizedAttr>.<Method>(...)` where
  `<CapitalizedAttr>` is not `project` (e.g. FLExProject.py's
  `self.LexEntry.Create(...)`, `self.Senses.Delete(...)` in the `Lexicon*`
  convenience wrappers). This is a call-site exclusion, not a
  whole-method one -- `LexiconDeleteObject` still gets flagged for its
  genuine `collection.Remove(obj)` / `obj.Delete()` fallback branch even
  though its dispatch branches (`self.LexEntry.Delete(obj)`, etc.) are
  individually excluded. Delegation through a local alias (e.g.
  `sense_ops = self.project.Senses; sense_ops.MergeObject(...)` in
  `LexEntryOperations.__DeduplicateSensesInEntry`) does **not** match this
  rule and is correctly still counted, matching the cycle-1 table.
- `TsStrBldr` builder calls: `.Clear()`/`.Replace(...)` on a local var
  whose name contains "bldr" (case-insensitive).
- `SandboxGenericMSA` field assignments: tracked explicitly (variable
  bound to `SandboxGenericMSA()` -> its later `.Field = ...` assignments
  are excluded from the property-suffix rule). This had to be made
  explicit rather than left implicit: `SandboxGenericMSA.MainPOS` and
  `.SecondaryPOS` both coincidentally end in `"OS"`, so a naive
  suffix-only rule produced 3 false positives
  (`MSAOperations.CreateStem/CreateInflAff/CreateUnclassifiedAffix`)
  before this tracking was added.

## Did the scanner reproduce 294? No -- 295, with one reconciled, reported
discrepancy (not tuned away)

First pass produced 296 (2 short of the table, 4 over). Diffing by
`(file, class, method)` identity against every row of
`cycle1-explore-b2sweep.md` found and fixed three real scanner bugs:

1. **Missed:** `PhonologicalRuleOperations.__ClearSequence` uses
   `seq.RemoveAt(seq.Count - 1)`, not `.Remove(...)` -- added `RemoveAt` as
   an indicator (labelled `.Remove` to match the table).
2. **Missed:** `ScrSectionOperations.Create` calls
   `factory.CreateScrSection(...)`, not `factory.Create(...)` -- added the
   narrow `<factory-var>.Create<Suffix>` match described above.
3. **False positives (3):** `MSAOperations.CreateStem`/`CreateInflAff`/
   `CreateUnclassifiedAffix` were flagged for `sandbox.MainPOS = ...`
   because `MainPOS` ends in `"OS"` by coincidence of English abbreviation
   (Part-Of-Speech), not LCM `OwningSequence` convention -- fixed via the
   explicit `SandboxGenericMSA` variable-tracking exclusion above.

After those three fixes the scanner's output is a byte-for-byte identity
match against all 294 cycle-1 rows (`only_in_reference = 0`), **plus one
extra finding not in the cycle-1 table**:

```
('FLExProject.py', 'FLExProject', 'SetAudioPath')
```

**This is a genuine discrepancy, reported rather than suppressed.**
`FLExProject.SetAudioPath` (current source, not cycle-1-era) ends with:

```python
bldr = self.project.ServiceLocator.GetInstance("TsStrBldr")
bldr.Clear()
bldr.Replace(0, 0, "￼", None)
...
multistring_field.set_String(wsHandle, bldr.GetString())
```

no `with self._TransactionCM(...)` anywhere in the method. The `bldr.Clear()`
/ `bldr.Replace(...)` calls are correctly excluded by the TsStrBldr-builder
rule. But `multistring_field.set_String(wsHandth, bldr.GetString())` is a
real, unbracketed `set_String` call on a genuine LCM multistring field
parameter -- structurally identical to the `set_String` calls in
`FLExProject.LexiconSetFieldText`/`LexiconClearField`, both of which
**are** counted in the cycle-1 table (as `needs-review`, but counted).

Cycle-1's own "Ambiguous cases" note for this method reads: *"only
bldr.Clear() / bldr.Replace(...) on a TsStrBldr; the resulting string is
handed to a setter elsewhere. Excluded from the count."* That description
does not match the code as it stands today -- the setter call
(`multistring_field.set_String(...)`) is inside this same method, not
"elsewhere." Applying the same rule used everywhere else in the table
(any `set_String`/`SetString` call outside a `with self._TransactionCM`
block counts, confidence `needs-review` if the object's exact LCM type
isn't statically known), this method should have been counted. I read
this as a cycle-1 documentation oversight, not a difference in what the
methodology should classify -- and per the task instructions I did not
special-case the scanner to hide the mismatch.

**Recommendation for the lead:** add `FLExProject.SetAudioPath` to B2's
scope (likely the FLExProject/code-root batch) and bump the domain-batch
total in `tasks.md`'s B2 line from 294 to 295 (code-root 13 -> 14) when
that batch is planned.

## Baseline format

`tests/write_path_transactions/snapshots/unbracketed_baseline.json`:

```json
{
  "total": 295,
  "entries": [
    {
      "file": "BaseOperations.py",
      "line": 516,
      "class_name": "BaseOperations",
      "method_name": "Sort",
      "kinds": [".MoveTo"]
    },
    ...
  ]
}
```

Identity for ratchet comparison is `(file, class_name, method_name)` --
deliberately **not** including `line`, since line numbers drift whenever
unrelated code above a method is edited and the ratchet must not fire on
line-number churn alone. `kinds` is informational (which indicator(s)
triggered the finding), not part of the identity key.

## How the ratchet works in both directions

`test_unbracketed_mutations.py`, four tests:

1. `test_scanner_runs_and_finds_entries` -- sanity check the scanner isn't
   silently returning zero (would mask "scanner is broken" as "B2 is
   done").
2. `test_no_new_unbracketed_mutations` -- **forward guard.** Computes
   `current = scan()` live, diffs its keys against the baseline's keys.
   Any key present in `current` but absent from the baseline is a NEW
   violation (never-bracketed-in-the-first-place addition, or a
   regression of something previously bracketed) and fails the test,
   printing file:line, class.method, the kind(s) found, and an explicit
   fix instruction (`wrap ... in with self._TransactionCM("<label>"):
   and remove its entry from unbracketed_baseline.json`).
3. `test_baseline_ratchets_down_as_sites_are_bracketed` -- **reverse
   guard.** Diffs the other direction: any baseline key no longer present
   in `current` (i.e. it got bracketed by a landed B2 batch) fails the
   test, by design, forcing the baseline file to be hand-edited down as
   part of that batch's commit. This is what keeps "294 (now 295) -> 0"
   an auditable countdown instead of a promise: the baseline can only
   shrink, and only via a deliberate edit.
4. `test_baseline_total_matches_entry_count` -- guards the baseline
   artifact's own internal consistency (`total` field vs. `len(entries)`).

Net effect confirmed by manual fault injection during this session (not
left in the tree): removing one real entry from a scratch copy of the
baseline made test 2 fail with a clear "NEW unbracketed... wrap in
`with self._TransactionCM(...)`" message; appending one fake
already-bracketed entry made test 3 fail with a clear "already bracketed
and must be REMOVED from unbracketed_baseline.json" message. Baseline was
regenerated fresh from the scanner afterward, so the checked-in artifact
reflects the real current tree, not a scratch/test state.

## Pytest result (current tree)

```
tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_scanner_runs_and_finds_entries PASSED
tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_no_new_unbracketed_mutations PASSED
tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_baseline_ratchets_down_as_sites_are_bracketed PASSED
tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_baseline_total_matches_entry_count PASSED
4 passed
```

Green at 295 known, 0 new -- red-to-baseline-green as specified (294 was
the target; 295 is what the tree actually contains today, with the extra
entry explained above rather than hidden). As B2 batches land, editing
`unbracketed_baseline.json` to drop bracketed entries is required for
`test_baseline_ratchets_down_as_sites_are_bracketed` to keep passing --
that's the ratchet operating as designed, not a bug to route around.

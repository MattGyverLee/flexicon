<!-- Provenance: main session wrote this file because lex-qc cannot write files. Content is the lex-qc hand-back verbatim. -->

**QC #255 — `0672b0b` — 95/100 — approve.** No P0, P1, or P2. Pattern-audit skip accepted (new wrapper).

`CreateAffixSlot` (`POSOperations.py:901`) and `AddSlotToTemplate` (`MorphRuleOperations.py:467`) both call `_EnsureWriteEnabled` before any mutation. Null `pos`/`name` and null `template`/`slot`/`side` go through `_ValidateParam` (`FP_NullParameterError`). Blank names, unknown sides, owner mismatch, and a non-integer index raise `FP_ParameterError`. Read-only raises `FP_ReadOnlyError`. No `flexlibs2` string in the diff.

Attach-before-write matches `POSOperations.Create` (`:227`) and `InflectionFeatureOperations.TypeCreate` (`:698`): one `_TransactionCM` (`POSOperations.py:914-923`) does `factory.Create()`, `AffixSlotsOC.Add`, then `Name.set_String` and `Optional`. The offline log asserts `create, add, makestring, name, optional`.

`bool` is rejected as an index at `MorphRuleOperations.py:501` (`isinstance(index, bool)` before the `int` check, so `True` cannot insert at 1). Docstrings name `project.POS.CreateAffixSlot` (`POSOperations.py:875`) and `project.MorphRules.AddSlotToTemplate` (`MorphRuleOperations.py:436`). `docs/FUNCTION_REFERENCE.md:60-66` sits those rows beside `GetAffixSlots`. `docs/USAGE_AFFIX_TEMPLATES.md:76-78` uses the same accessors.

Live evidence is real: `run_mode` live, pre-state slot count 0 / prefix count 0 on POS HVO 2706, post-state re-read name `TEST_PossConcord`, `Optional` false, prefix HVOs `10444, 10442` after insert-at-0. Index 99 left that order unchanged.

**Prefix plus `optional=False` only is not P2.** `False` is the write that differs from a true default, and it was re-read from a fresh `GetAffixSlots` object. `optional=True` is the same setter. Suffix, proclitic, and enclitic are the same `Add`/`Insert` on another reference sequence; the side map is the four-entry dict at `MorphRuleOperations.py:60`. No broken or silent path was shown. Residual coverage only.

Non-blocking: no test passes `index=True` or `index=False`, and proclitic/enclitic have no positive routing assertion. The live test also writes untracked `specs/255-affix-slot/evidence/_live_measurements.json`.

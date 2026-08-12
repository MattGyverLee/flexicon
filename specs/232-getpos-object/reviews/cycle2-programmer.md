# Cycle 2 - Programmer report: issue #232 (GetPartOfSpeechObject)

## Diff (flexicon/code/Lexicon/LexSenseOperations.py)

```diff
-from ..lcm_casting import cast_to_concrete
+from ..lcm_casting import cast_to_concrete, get_pos_from_msa
...
+_POS_BEARING_MSA_CLASSES = frozenset(
+    {"MoStemMsa", "MoInflAffMsa", "MoDerivAffMsa", "MoUnclassifiedAffixMsa"}
+)
...
     Returns:
-        IPartOfSpeech | None: ... derivational-affix variant that exposes only
-        FromPartOfSpeechRA / ToPartOfSpeechRA (issue #87 ...).
+        IPartOfSpeech | None: The POS object for all four recognized
+        MSA subtypes ... For MoDerivAffMsa this is the output category
+        (ToPartOfSpeechRA), consistent with SetPartOfSpeech. Returns
+        None if the sense has no MSA, or if the MSA's subtype is not
+        one of the four recognized POS-bearing types (a warning is
+        logged in that case).
...
     msa = sense.MorphoSyntaxAnalysisRA
     if msa is None:
         return None
-    return getattr(msa, "PartOfSpeechRA", None)
+
+    class_name = getattr(msa, "ClassName", None)
+    if class_name not in _POS_BEARING_MSA_CLASSES:
+        logger.warning(
+            "GetPartOfSpeechObject: sense Hvo=%s has an MSA with "
+            "unrecognized ClassName=%r; no POS-bearing property "
+            "exists on this subtype",
+            getattr(sense, "Hvo", None),
+            class_name,
+        )
+        return None
+
+    return get_pos_from_msa(msa)
```

`logger` (module-level) and `get_pos_from_msa` import already existed / were added; `GetPartOfSpeech` (line ~1142, InterlinearAbbr) left untouched per R3.

## Pytest output

`python -m pytest tests/test_lexsense_getpos_object.py -v`

11 passed in 1.54s. All AST tests (no stale `getattr(msa, "PartOfSpeechRA", ...)`, delegates to `get_pos_from_msa`, import present, `_POS_BEARING_MSA_CLASSES` == exactly the four names, stale #87 docstring language gone) and all mock-behavior tests (no-MSA -> None/no warn; unrecognized ClassName -> None + warn naming ClassName; each of the four recognized classes -> delegated value, no warn) passed.

## Deviations

- New test file avoids importing the real module (which transitively pulls in `SIL.LCModel`/pythonnet) even though this dev box happens to have FieldWorks installed. Behavioral tests instead extract `GetPartOfSpeechObject`'s own AST subtree plus `_POS_BEARING_MSA_CLASSES`, exec them into an isolated module, and patch `get_pos_from_msa`/`logger` there. This is stricter than the letter of "patch `get_pos_from_msa`" (no real import to patch against) but preserves the stated requirement that the suite run with no FieldWorks install present, matching `test_agent_version_unicode.py`'s guarantee. Exercises the real, unmodified method body.
- Warning message wording/format is not specified by the ticket; chose a single `logger.warning(...)` call naming both `sense.Hvo` and the unrecognized `ClassName`, per R4b.

No other deviations. Only `LexSenseOperations.py` and the new test file were touched; no commit made.

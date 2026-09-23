# Issue #263 -- offline verification

## /lex-lead ruling

- **Fix shape:** Correct `FLExProject.pyi` to declare `writeEnabled: bool` (lowercase), matching runtime `FLExProject.py` and CLAUDE.md.
- **No runtime alias:** Do not add a `WriteEnabled` property on `FLExProject`; no in-repo callers use the capitalized form, and an alias would preserve the wrong discoverability surface for new codegen.
- **Scope:** Single stub field; pattern audit found no other `.pyi` files declaring `WriteEnabled: bool`.

## Commands

```
python3 -m pytest tests/test_write_enabled_fix.py -m "not requires_live_project" -q
python3 -m pytest tests/test_pyi_return_annotation_ratchet.py -m "not requires_live_project" -q
```

## Result

Pure typing/stub change -- live LCM verification not applicable per CLAUDE.md.

**PASS:** stub corrected; ratchet test added; offline pytest green (see CI on PR).

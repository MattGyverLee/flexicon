# Issue #281 -- lex-lead ruling

**Date:** 2026-09-23  
**Branch:** fix/281-lcm-casting-logger from origin/main

## RULING (binding)

The `import logging` line inside the `lcm_casting.py` module docstring is a
defect: it never executes, so the module has no `logger` despite CLAUDE.md
convention.

**Correct behaviour (issue #281 scope):**

1. Move `import logging` to module scope immediately after the closing
   docstring delimiter.
2. Add `logger = logging.getLogger(__name__)`.
3. On `cast_to_concrete` no-op paths where `ClassName` is present but not
   registered in `_interface_cache`, emit a single `logger.debug` line (not
   warning -- totality is intentional; this aids #279-class diagnosis).
4. Do **not** change cast behaviour, registry contents, or raise on unknown
   types.

**Out of scope:** Registering the four #279 interfaces, changing
`cast_to_concrete` totality, or adding info/warn on successful no-op casts
when `ClassName` is missing.

## Verification plan

- Offline: AST/source ratchet that `import logging` is not inside the module
  docstring and `logger = logging.getLogger(__name__)` exists; run targeted
  pytest without live LCM.
- Live: not required (no LCM write path).

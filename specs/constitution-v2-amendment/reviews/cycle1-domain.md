# Domain Expert Review — Constitution v2.0.0, Principle VII

Cycle 1. Reviewer: lex-domain. Date: 2026-09-22.

Note: produced with Read/Grep/Glob only; persisted to this path by the main
session because the reviewing agent has no Write tool.

**Verdict: sound-with-amendments.** The additive/mutative split is the right shape
for "hardening without a brake on growth," but the text under-specifies scope in
three places that would, as written, either (a) silently fail to protect the thing
it claims to protect (wrapper surfaces), (b) accidentally over-freeze internal
helpers and chill ordinary refactors, or (c) bless the exact anti-pattern Rule 5
forbids. None require reversing the additive/mutative distinction itself.

## Defects

**1. VII's additive-kwarg clause conflicts with `API_DESIGN_PHILOSOPHY.md` Rule 5.**
VII: "new keyword arguments whose defaults preserve current behavior" are
unrestricted, no gate. Rule 5's own example (`SetText(preserve_whitespace=False)`)
is a *new* kwarg whose default preserves current (buggy) behavior — precisely what
VII just exempted. Cause #2 ("preserved a defect behind a default") does not rescue
this: cause #2 only fires for the *mutative* bucket (changing an existing default),
and a brand-new kwarg never reaches that bucket under VII as literally written — it
is additive by definition, full stop. A future agent can add exactly the
anti-pattern Rule 5 names and cite VII to skip the gate entirely.

*Fix:* append to the additive clause: "— except a new keyword argument whose
default reproduces behavior Principle V would call a defect; such a kwarg must
default to corrected behavior, with the buggy path reachable only by explicit
opt-in (mirrors Rule 5)."

**2. Surface-snapshot text gives no account of `__getattr__`-routed surfaces.**
`LCMObjectWrapper.__getattr__` (`flexicon/code/Shared/wrapper_base.py:124-174`) and
`PythonicWrapper.__getattr__` (`flexicon/code/PythonicWrapper.py:79-112`) forward
arbitrary attribute names to the underlying LCM object at runtime. Neither overrides
`__dir__`, so no static AST scan or `dir()`-based reflection can enumerate
`wrapped.RightHandSidesOS` or `entry.Senses` as members of the class — they do not
exist as Python-level names anywhere in the source. A baseline generator can only
see the ~6 explicit members (`class_type`, `lcm_object`, `AsICmObject`,
`get_property`, dunders). VII says "working user code must survive any of these
untouched," but for the vast majority of what a wrapped object actually exposes,
there is no mechanism that can even notice regression — the ratchet is structurally
blind here, not falsely "frozen." This is not a bug in VII's philosophy (liblcm
removals here are already excused under cause #1), but the text currently implies
uniform mechanical coverage it cannot deliver.

*Fix:* add one sentence to the snapshot paragraph: "The baseline covers only
statically declared names; `__getattr__`-forwarded LCM properties on wrapper classes
are out of its reach and are governed instead by the liblcm contract baseline and
cause #1."

**3. No declared public/internal boundary — a baseline built the obvious way would
over-freeze.** `flexicon/__init__.py` has no `__all__`; "published" is defined only
by "is it imported at module level in `__init__.py`." That rule is real (confirmed
by the module's own comments — `cast_to_concrete` is imported with an explicit
"public since #271" comment, `HeadlessLcmUI` likewise) but it is stated only in
`CLAUDE.md` prose and code comments, never in the constitution. Meanwhile
`flexicon/code/lcm_casting.py` has ten-plus non-underscore, fully-docstringed
functions (`cast_all`, `clone_properties`, `validate_merge_compatibility`,
`get_pos_from_msa`, `get_inflection_class_from_msa`, `set_inflection_class_on_msa`,
`get_common_properties`, `get_concrete_type_properties`, `cast_phonological_rule`,
`get_from_pos_from_msa`, plus module-level constants `POS_BEARING_MSA_CLASSES`) that
are internal by convention but indistinguishable by name from `cast_to_concrete`. A
baseline generator built by "scan for non-underscore names" — the naive reading of
"exported names... of the public API" — would freeze all of these, gating routine
internal refactors behind `BREAKING CHANGE:` footers. That is a direct brake on
growth, the thing the user explicitly does not want.

*Fix:* state in VII or the snapshot paragraph: "'Published' means bound in
`flexicon/__init__.py`'s namespace (add an explicit `__all__` there as the single
source of truth) plus the public methods of the classes so exported. A name
reachable only via `flexicon.code.*` is internal regardless of underscore usage."

**4. Undefined scope relative to the `flexlibs2` shim.** The snapshot text does not
say whether the baseline covers `flexlibs2` too. Since the shim re-exports
`flexicon` names, a repo-wide scan would double-track the same symbols under a
second, deliberately-temporary "published surface," adding `BREAKING CHANGE:`
bookkeeping to the v5.0.0 removal that `CLAUDE.md` and
`tests/test_flexlibs2_alias_ratchet.py` already fully govern. Not a deadlock (cause
#3 cleanly authorizes the removal either way — the shim has been present and warned
since the rename), but redundant.

*Fix:* one sentence: "The baseline tracks only the `flexicon` package; `flexlibs2`'s
v5.0.0 removal is governed by `CLAUDE.md` and the alias ratchet, not this baseline."

## Public/internal boundary — answered

No `__all__`, no reliable naming convention (underscore is not consistently applied
— see defect 3). The only real signal is membership in `flexicon/__init__.py`'s
import list, corroborated by CLAUDE.md ("`cast_to_concrete` is public... the rest...
is internal") and the `cast_to_concrete` docstring's explicit "**Public API.** Import
it as: `from flexicon import cast_to_concrete`" (`lcm_casting.py:519-521`). This
boundary works today but is undocumented as a *rule* and unenforced mechanically.
Recommend codifying it via `__all__` per defect 3's fix.

## Gate 5's "need only a regenerated baseline" — intentional, not a hole

Confirmed by design: VII exists specifically to leave growth ungated ("unrestricted
and needs no gate"). The forward-regeneration is deliberately record-only; the real
gate is the backward check on *removed* entries, which still fires correctly on a
disguised rename (rename = remove old name + add new name; the removal half still
fails backward without a footer). So this is sound as designed — but the current
wording ("need only a regenerated surface baseline") reads ambiguously as if nothing
is checked.

*Fix:* append "(the forward pass never blocks; only removed/changed entries can fail
a commit)."

Separately: `Glob` confirms **no surface-baseline file or generator exists anywhere
in the repo yet** — VII/Gate 5 describe a control not yet built, which is prose, not
a control, per Principle III's own standard. Flag as implementation debt to track
alongside this amendment, not a defect in the rule's wording.

## Files referenced

- `.specify/memory/constitution.md` (subject of review)
- `flexicon/__init__.py`
- `flexicon/code/Shared/wrapper_base.py`
- `flexicon/code/PythonicWrapper.py`
- `flexicon/code/Shared/smart_collection.py`
- `flexicon/code/lcm_casting.py`
- `tests/test_flexlibs2_alias_ratchet.py`
- `docs/API_DESIGN_PHILOSOPHY.md`

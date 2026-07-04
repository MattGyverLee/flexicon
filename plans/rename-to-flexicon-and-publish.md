# Plan: Rename flexlibs2 → flexicon, Publish to PyPI, Sync the MCP

**Status:** Draft for approval
**Scope:** Two repos — `flexlibs2` (→ becomes `flexicon`) and `FlextoolsMCP`
**Distribution name:** `pyflexicon` (bare `flexicon` is squatted on PyPI by an abandoned 2017 project)
**Import name:** `flexicon`
**License:** LGPL-2.1 — Craig Farrow copyright + notice retained (non-negotiable, independent of rename)

---

## Guiding decisions (already made)

- Stop being a *fork* of cdfarrow/flexlibs; keep a *compatibility facade* so FlexTools/FlexTrans can adopt flexicon as a superset.
- `flexlibs2` remains a working import alias for **one deprecation cycle** (grace period for on-disk user scripts), removed at flexicon **v5.0.0**.
- User controls the MCP → do a **synced release**; collapse the deferred MCP layers into one coordinated cutover.
- Automation = **PyPI Trusted Publishing via GitHub Actions (OIDC)**. No PyPI MCP needed or used.

## Versioning

- First flexicon release: **`4.1.0`** — rename + alias shim; nothing breaks because the alias holds, so semver stays honest (minor, not major).
- **`5.0.0`** reserved for *removal* of the `flexlibs2` alias (the actual breaking change), later.

---

## Pre-flight (verify before touching anything)

- [ ] **P1.** Confirm `pyproject.toml` current contents & build backend; reconcile with `setup.cfg` (two packaging files present — collapse to one, pyproject-only).
- [ ] **P2.** Resolve the `flexlibs2.FLExLCM` vs `flexlibs2.code.FLExLCM` discrepancy (MCP `project_discovery.py:129` imports the former; file lives at the latter). Determine if it's dead/legacy/stable-flavor code. Fix or confirm harmless.
- [ ] **P3.** Grep the MCP for every literal `flexlibs2` occurrence and bucket into the 4 layers (runtime import / flavor-key / generated-output / index-namespace). Produce the authoritative change list.
- [ ] **P4.** Confirm ownership of the `flexlibs2` name on PyPI (earlier check returned 404 — may be unregistered, not owned). Decide whether to also publish a `flexlibs2` meta-package or skip it.
- [ ] **P5.** Clean stray build artifacts: `flexlibs.egg-info/` (old fork name) and `flexlibs2.egg-info/` — remove; they should not ship.

---

## Phase 1 — flexicon repo (rename + package + release)

Ordering matters: **flexicon must publish before the MCP can pin it.**

- [ ] **1.1** Rename package dir `flexlibs2/` → `flexicon/`. (Relative imports survive; no internal import edits needed.)
- [ ] **1.2** Update `flexicon/__init__.py` header comment (name line) — keep `version = "4.1.0"`.
- [ ] **1.3** Add compat shim so `import flexlibs2` (and deep paths) keep working:
      create `flexlibs2/__init__.py` (a tiny separate top-level package) doing:
      ```python
      import sys, warnings
      import flexicon
      sys.modules["flexlibs2"] = flexicon           # flexlibs2.X.Y -> flexicon.X.Y
      warnings.warn("flexlibs2 renamed to 'flexicon'; update imports. "
                    "Alias removed in v5.0.0.", DeprecationWarning, stacklevel=2)
      ```
- [ ] **1.4** `pyproject.toml`:
      - `name = "pyflexicon"`, `version = "4.1.0"`, `requires-python`, `license = "LGPL-2.1"`, authors, description, project URLs.
      - build backend (keep current if hatchling/setuptools; wheel packages = `flexicon` **and** the `flexlibs2` shim).
      - Ensure `py.typed` and `__init__.pyi` ship (package data).
- [ ] **1.5** Delete `setup.cfg` (fold anything needed into pyproject) OR keep minimal — pick one source of truth.
- [ ] **1.6** Update `README.rst`: new name, `pip install pyflexicon`, `import flexicon`, "began as a fork of cdfarrow/flexlibs (LGPL-2.1), now an independent successor" paragraph, alias-deprecation note.
- [ ] **1.7** Update `LICENSE.txt`/add `NOTICE`: keep Farrow copyright, add your copyright line.
- [ ] **1.8** Retire fork machinery. **CORRECTION after inspection:** the three `.github/workflows/*compat*/*monitor*` files all track **LibLCM (FieldWorks) — the REAL upstream — and STAY.** None are cdfarrow-parity. Fork severance is only: (a) git `origin` remote (repoint to your repo, drop/rename cdfarrow remote), (b) convert `history.md` from upstream-sync mirror to plain changelog / fold into `CHANGELOG.md`, (c) attribution/README framing. Leave CI untouched (optionally de-`flexlibs`-ify path/job names later — cosmetic).
- [ ] **1.9** Add `.github/workflows/publish.yml` (Trusted Publishing, tag-triggered — see Appendix A).
- [ ] **1.10** Local build + smoke: `python -m build`; in a fresh venv `pip install dist/*.whl`; assert `import flexicon; flexicon.version == "4.1.0"` and `import flexlibs2` warns + resolves `flexlibs2.code.lcm_casting`.
- [ ] **1.11** **TestPyPI dry run** first: register Trusted Publisher on test.pypi.org, tag a pre-release, confirm the workflow uploads cleanly and `pip install -i testpypi pyflexicon` works.
- [ ] **1.12** Register the production Trusted Publisher on pypi.org (project → Publishing → GitHub: repo + `publish.yml` + environment `pypi`).
- [ ] **1.13** Tag `v4.1.0`, push → workflow publishes `pyflexicon 4.1.0` to PyPI. Verify `pip install pyflexicon`.
- [ ] ~~**1.14** publish `flexlibs2` meta-package~~ — **DECIDED: skip.** Import alias only; the MCP (only real consumer) pins `pyflexicon` directly. No `flexlibs2` dist on PyPI.

## Phase 2 — FlextoolsMCP repo (pin flexicon, cut over all 4 layers)

- [ ] **2.1** Bump the MCP's flexicon dependency/path to `pyflexicon>=4.1.0`.
- [ ] **2.2** **Layer 1 (runtime imports):** `kernel.py`, `handlers/execution.py`, `casting_helpers.py`, `undo_subprocess.py`, `flexlibs2_analyzer.py`, `project_discovery.py` → `flexicon`.
- [ ] **2.3** **Layer 4 (index namespaces):** flip `flexlibs2_analyzer.py:1305` prefix `flexlibs2.code.` → `flexicon.`; reindex; regenerate `*_api_v4.1.0.json`.
- [ ] **2.4** **Layer 3 (generated output):** templates (`2-flexlibs2-template.py`, `3-liblcm-template.py`), `worked_examples.py`, `execution.py:217` injection map, `tool_definitions.py`, THREE_TIER_INJECTION, style-guide docs → emit `from flexicon import`.
- [ ] **2.5** Retire the flexlibs-vs-flexlibs2 **shadowing guard** (`validators.py:1130` and related) — the name collision it defended against no longer exists after rename.
- [ ] **2.6** **Transition safety:** widen `validators.py:827` implicit-discovery regex to accept **both** `from flexlibs2 import` and `from flexicon import` (emit flexicon, accept either) so users' on-disk scripts still validate.
- [ ] **2.7** **Layer 2 (flavor key) — DECIDED: rename.** Rename `"flexlibs2"` → `"flexicon"` across `session_mode` / `include_flexlibs2` / `--flexlibs2-only` / `api_index.flexlibs2`, the index JSON key, and all tests asserting on them. Full consistency; no legacy label.
- [ ] **2.8** Rename `flexlibs2_analyzer.py`, `check_flexlibs2_ops.py`, `refresh.py --flexlibs2-only` flag consistently with 2.7.
- [ ] **2.9** Update MCP `CLAUDE.md`, `USAGE.md`, `DEVELOPMENT.md`, docs to flexicon.
- [ ] **2.10** Run MCP test suite; fix `test_canonical_intents.py` / `test_rejection_payloads.py` namespaces.

## Phase 3 — Release & verify (synced)

- [ ] **3.1** flexicon `v4.1.0` on PyPI (Phase 1) — must land first.
- [ ] **3.2** MCP release pinning `pyflexicon>=4.1.0` — tag/release after 3.1 is live.
- [ ] **3.3** End-to-end smoke: MCP generates a script → it uses `from flexicon import` → runs against a real FLEx project → passes. Confirm no `flexlibs2` shadowing warnings appear.
- [ ] **3.4** Re-task the LEX crew: `lex-author` → compat-facade guardian (does the legacy surface + alias still work?); `lex-archivist` → drop upstream-sync-mirror duty, keep changelog/release cuts.

## Later (separate, deliberate) — v5.0.0

- [ ] Remove the `flexlibs2` alias shim; drop the dual-accept validator regex; retire the `flexlibs2` meta-package. Announce in advance.

---

## Appendix A — publish.yml (Trusted Publishing, no secrets)

```yaml
name: publish
on:
  push:
    tags: ["v*"]
jobs:
  release:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write        # OIDC — no API token stored
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.x" }
      - run: pipx run build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

## Open questions for the user

1. ~~**Layer-2 flavor key (2.7):**~~ **DECIDED — rename `"flexlibs2"` → `"flexicon"` everywhere in the MCP.**
2. ~~**flexlibs2 PyPI meta-package:**~~ **DECIDED — skip. Import alias only; no `flexlibs2` dist on PyPI.**
3. ~~**GitHub repo rename:**~~ **DECIDED — rename repo to `flexicon` (`gh repo rename flexicon`); GitHub auto-redirects the old URL. Update local remotes after.**

**All open questions resolved. Plan ready to execute.**
```

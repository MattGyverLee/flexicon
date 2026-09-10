# Releasing flexicon

The release runbook for `pyflexicon`. Cutting a release is mostly
bookkeeping plus **one irreversible action**: pushing a `v*` tag, which
publishes to PyPI automatically.

Read the whole of section 1 before you start. A version number, once
published to PyPI, can never be re-used -- only yanked.

---

## 1. What actually publishes

Two workflows fire on two *different* events. Both are needed for a
complete release, and neither triggers the other.

| Workflow | Trigger | Effect |
|----------|---------|--------|
| `.github/workflows/publish.yml` | `push` of a tag matching `v*` | Builds sdist + wheel, publishes to **PyPI** |
| `.github/workflows/publish-docs.yml` | GitHub **Release** `published` | Builds Sphinx docs, pushes to `gh-pages` |

**Pushing a bare tag publishes the package but leaves the documentation
site stale.** A release is only complete once a GitHub Release object
also exists. The two steps are separate on purpose -- see section 5.

> ### PARTIALLY REPAIRED after v4.6.0: the docs half needs a runner
>
> `publish-docs.yml` has never successfully published. It has failed three
> separate ways, and every one of them was silent from the release's point
> of view -- PyPI still gets the package, so the release *looks* complete.
> Defect 3 is the one to read first: for the whole of the v4.7.0 cut the
> workflow file was invalid, so no trigger in it fired at all.
>
> 1. **No runner. STILL OPEN -- needs an infrastructure decision.** The
>    build job declares `runs-on: [self-hosted, windows, fieldworks]`, and
>    the repository has **zero self-hosted runners registered**
>    (`gh api repos/MattGyverLee/flexicon/actions/runners` ->
>    `"total_count": 0`). The job therefore queued until GitHub's 24-hour
>    limit and was auto-cancelled: v4.3.0 and v4.4.0 both show `cancelled`
>    after `24h0m`, and the v4.6.0 run was cancelled by hand once the
>    cause was found.
>
>    FieldWorks is genuinely required, so this cannot simply move to
>    `ubuntu-latest`: `import flexicon` runs `FLExInit` at import time,
>    which calls `FLExGlobals.InitialiseFWGlobals()` (a Windows-registry
>    probe) and then `clr.AddReference("FwUtils")` at module scope.
>    `autodoc_mock_imports` cannot satisfy either, because both are
>    executed statements rather than imports. Two real options:
>    **(a)** register a Windows runner with FieldWorks 9+ and the labels
>    `self-hosted`, `windows`, `fieldworks` (Settings > Actions >
>    Runners) -- this also un-blocks `upstream-compatibility-check.yml`,
>    which targets the same empty pool; or **(b)** give `FLExInit` an
>    import-time bypass so the docs can build without FLEx, accepting
>    that autodoc then renders mocked rather than real LCM signatures.
>
>    A `preflight` job on `ubuntu-latest` is meant to run first and fail
>    fast when no matching runner is online. **Do not believe the claim
>    this box used to make that it does so.** Between `fe556d3`
>    (2026-09-08) and the v4.7.0 cut it never ran even once, and neither
>    did anything else in the file -- see defect 3 below. Today it is
>    reachable again but *inert by default*: reading the runner registry
>    needs admin rights `GITHUB_TOKEN` cannot hold, so unless a
>    `RUNNER_REGISTRY_TOKEN` secret (a PAT with `administration:read`) is
>    configured, the step fail-opens with a warning and the build queues
>    for the full 24 hours exactly as before. **Assume a docs run still
>    burns 24 hours until a runner is registered.**
>
> 2. **The Sphinx build itself crashed. FIXED.** `sphinx-build
>    docs/sphinx flexicon/docs/flexiconAPI` died with an unhandled .NET
>    exception partway through `api/flexicon.code` --
>    `Python.Runtime.PythonException: name must be a str, not a NoneType`,
>    thrown from `Python.Runtime.MethodBinding.get_Signature()`.
>
>    Root cause, isolated to a single member:
>    `flexicon.code.headless_ui.HeadlessLcmUI` subclasses an LCM interface
>    *and* sets `__namespace__ = "Flexicon.Headless"`, which makes
>    pythonnet emit a real derived .NET type
>    (`Flexicon.Headless.HeadlessLcmUI`, in the `Python.Runtime.Dynamic`
>    assembly). pythonnet's IL emitter never calls
>    `MethodBuilder.DefineParameter`, so the emitted
>    `Equals(System.Object)` override has `ParameterInfo.Name == null`.
>    autodoc formats every member's signature, which reads
>    `__signature__`; pythonnet answers from `MethodBinding.get_Signature()`,
>    which passes the null name to `inspect.Parameter()`. Because the
>    raise happens inside the native `tp_getattro` slot it escapes as an
>    unhandled CLR exception and **aborts the process** -- exit 127, no
>    Python traceback, no Sphinx warning. A bare `ILcmUI` subclass with no
>    `__namespace__` does *not* reproduce it; only the emitted type does.
>
>    The fix is an `autodoc-skip-member` guard in `docs/sphinx/conf.py`
>    that skips members whose type lives in pythonnet's `CLR`
>    pseudo-module. Those are exactly the inherited/emitted CLR plumbing
>    (`Equals`, `GetHashCode`, `GetType`, `ToString`, `MemberwiseClone`,
>    `Finalize`) -- no docstrings, no API value. `HeadlessLcmUI` and all
>    15 of its real `ILcmUI` members still render. Pinned by
>    `tests/test_sphinx_conf_clr_skip.py`.
>
>    **The 3.12-vs-3.11 caveat from the original report is closed.** The
>    crash was re-confirmed on Python **3.11.15 x64** with **pythonnet
>    3.1.0** and **Sphinx 9.0.4** -- the exact stack the workflow pins,
>    and a *newer* pythonnet than the 3.0.5 it was first seen on. It is
>    neither a 3.12 artifact nor fixed upstream. On that same environment
>    the patched build now completes: `build succeeded, 7 warnings`, 126
>    HTML pages. The 7 warnings are pre-existing docstring-indentation
>    nits in `FLExProject.OpenProject`, `MSAOperations`, and
>    `string_utils`; they do not fail the build.
>
> 3. **The workflow file was invalid, so NOTHING in it ran. FIXED.**
>    Ironic and worth remembering: the commit that added the fail-fast
>    preflight (`fe556d3`) is the commit that broke the workflow entirely.
>    It declared
>
>    ```yaml
>    permissions:
>      administration: read
>    ```
>
>    on the preflight job. `administration` is **not** a valid GitHub
>    Actions permissions scope (the valid set is `actions`, `attestations`,
>    `checks`, `contents`, `deployments`, `discussions`, `id-token`,
>    `issues`, `models`, `packages`, `pages`, `pull-requests`,
>    `repository-projects`, `security-events`, `statuses`), and a single
>    invalid key invalidates the **whole file** -- which un-registers every
>    trigger it declares, `release: published` included.
>
>    **How to recognise this class of failure**, because GitHub reports no
>    parse error anywhere obvious and simply stops honouring the file:
>
>    - `gh api repos/<owner>/<repo>/actions/workflows` returns the
>      workflow's **path** in the `name` field instead of its declared
>      `name:`. This is the fastest reliable check -- compare against the
>      other workflows, which show real names.
>    - Every push spawns a `failure` run **containing zero jobs**
>      (`gh api .../actions/runs/<id>/jobs` -> empty), on a workflow that
>      declares no `push` trigger at all.
>    - The events you *do* declare fire nothing. Here, run history shows
>      `release / cancelled` up to 2026-09-08T21:46Z, then only
>      `push / failure` from 22:16Z onward -- the first push after
>      `fe556d3`.
>
>    Consequence for the v4.7.0 cut: `gh release create` started **no docs
>    run whatsoever**. Section 5's note that step 5 "will drive the docs
>    build the moment a runner is registered" was false for that window.
>
>    **Before trusting any workflow edit, confirm the file still parses**
>    by checking that its `name` comes back from the API rather than its
>    path. `python -c "import yaml; yaml.safe_load(...)"` is *not*
>    sufficient -- this file parsed fine as YAML throughout; it was the
>    Actions schema it violated. `actionlint` catches invalid permission
>    scopes and is the right local gate.
>
> Until the runner exists, treat the documentation site as **manually
> maintained and currently stale**. A green release does not mean the API
> docs were refreshed, and -- until a `RUNNER_REGISTRY_TOKEN` secret is
> configured -- a docs run will still queue for 24 hours rather than
> reporting why. **Check the docs run explicitly after every cut**; do not
> infer it from a green PyPI publish.

PyPI upload uses **Trusted Publishing** (OIDC): `publish.yml` requests an
`id-token` and authenticates as the repo. There is no stored PyPI token
to rotate, and the `pypi` environment on GitHub gates the job.

### Workflows that do NOT gate a release

- `local-compat-check.yml` -- smoke tests on every push/PR to `main`.
  Ubuntu, Python 3.8/3.11/3.13. It parses the tree with `ast` and counts
  Operations classes; **it does not run the test suite** and cannot see a
  behavioural regression. Green here means "nothing is syntactically
  broken", nothing more.
- `upstream-api-monitor.yml` (daily), `upstream-compatibility-check.yml`
  (weekly) -- scheduled liblcm drift monitors, unrelated to a cut.

The real pre-release gate is the offline suite, run locally (section 3).
CI cannot run it: the suite needs FieldWorks and .NET, which no hosted
runner has.

---

## 2. Version numbering

`flexicon/__init__.py:15` is the **single** source of truth:

```python
version = "4.6.0"
```

`pyproject.toml` reads it dynamically (`version = { attr = "flexicon.version" }`),
so that one line is the only edit. Do not add a second version constant.

House convention, as practised, is not textbook SemVer:

- **Patch** (`4.5.1` -> `4.5.2`) -- a fix to a fix; no new API surface.
- **Minor** (`4.5.x` -> `4.6.0`) -- new public methods, **and behavioural
  breaking changes**. A repair to behaviour that was silently wrong ships
  as a minor bump, however visible the change, as long as no signature is
  removed and no default the caller passes explicitly changes meaning.
  Precedent: 4.4.0 (the `undoable=` default flip) and 4.6.0 (six
  behavioural breaks at once). Label each one
  `**BREAKING (behavioural): ...**` in the changelog and call them out in
  the release header note.
- **Major** -- reserved for **API-surface removal**. `v5.0.0` is
  pre-committed to the `flexlibs2` alias removal (see `CLAUDE.md` and
  `tests/test_flexlibs2_alias_ratchet.py`); do not spend that number on
  anything else.

### Check what is actually on PyPI first

The changelog is not proof of publication. Versions 4.5.0, 4.5.1 and
4.5.2 were fully changelogged, then never tagged -- `publish.yml` never
fired and none of them reached PyPI. That went unnoticed until the 4.6.0
cut. Always confirm:

```bash
python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('https://pypi.org/pypi/pyflexicon/json'))['info']['version'])"
git tag --sort=-v:refname | head -5
```

If the newest changelog section has no matching tag, it never shipped.
Fold its content into the release you are cutting and say so in the
header note rather than back-filling tags onto old commits.

---

## 3. Pre-release gate

Run from a clean tree on `main`, fully merged and pushed.

### The offline suite -- required

```bash
python -m pytest -m "not requires_live_project" -q
```

**Never run bare `pytest`,** and never `pytest --ignore=tests/contract`.
Neither applies an `-m` filter, so both collect and *execute* the
several-hundred `requires_live_project` tests in place against real FLEx
projects. The `-m` selector is the safety mechanism.

Record `passed` and `deselected` in the release notes. Both numbers move
legitimately as tests land; a *drop* in either is what matters. The
4.6.0 cut measured **1732 passed / 695 deselected**, superseding the
1291/483 baseline recorded at `33c5f7b`.

### Live LCM verification -- required only for write-path changes

A release cut is metadata (version, changelog, docs) and touches no LCM
call, so the cut itself needs no live run. The *changes being released*
do, and they should already carry their evidence under
`specs/<feature>/evidence/live-<task>.md` from when they landed. Verify
that evidence exists rather than re-running the live suite at cut time.

If you do need a live run:

```powershell
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest <file> -m requires_live_project -q
```

`FLEXLIBS_REQUIRE_LIVE=1` turns every silent degradation -- mock
fallback, locked project, missing fixture -- into a hard failure. Without
it a mock run passes green and proves nothing. Confirm
`tests/live_status.json` shows `"run_mode": "live"`.

### Build check

```bash
python -m build --outdir <scratch>/distcheck
```

Confirms sdist and wheel build before the tag makes it CI's problem.
`publish.yml` runs `pipx run build` on the same tree.

---

## 4. Cutting the release

Four files, one commit.

1. **`flexicon/__init__.py`** -- bump `version`.
2. **`CHANGELOG.md`** -- rename `## [Unreleased]` to
   `## [<version>] - <YYYY-MM-DD>`, add a `>` header note summarising the
   release and flagging any breaking change, and open a fresh empty
   `## [Unreleased]` above it.
3. **`history.md`** -- prepend a dated entry under `## History`
   (newest first). This is the narrative development log; `CHANGELOG.md`
   is the per-version record.
4. **`RELEASE_NOTES_v<version>.md`** -- the human-facing summary used as
   the GitHub Release body.

Commit with a `chore(release):` subject:

```bash
git commit -m "chore(release): cut <version> -- <one-line theme>"
```

> **Watch the commit-msg hook.** `.githooks/commit_msg_guard.py` blocks
> `close`/`fix`/`resolve` immediately before an issue number when used in
> *prose* -- a release commit that says "closes #251's review" will be
> rejected. Phrase around it. Enable the hook once per clone with
> `git config core.hooksPath .githooks`.

---

## 5. Publishing

Order matters. Push `main` first so the tag points at a commit that
exists on the remote.

```bash
# 1. main first
git push origin main

# 2. the tag -- THIS PUBLISHES TO PyPI
git tag v<version>
git push origin v<version>

# 3. watch it
gh run list --workflow=publish.yml --limit 1

# 4. verify PyPI actually has it
python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('https://pypi.org/pypi/pyflexicon/json'))['info']['version'])"

# 5. GitHub Release -- THIS PUBLISHES THE DOCS
gh release create v<version> --title "v<version> -- <theme>" --notes-file RELEASE_NOTES_v<version>.md
```

Step 5 is not optional. Skipping it leaves `gh-pages` serving the
previous version's API documentation against a shipped package.

**Today step 5 creates the Release but does not actually refresh the
docs** -- the Sphinx build is fixed, but no self-hosted runner exists to
run it on. Create the Release anyway: it is the durable record of the
version, carries the release notes, and will drive the docs build once a
runner is registered.

After step 5, **verify a docs run actually started**:

```bash
gh run list --workflow=publish-docs.yml --limit 3
```

Expect a row whose event is `release`. If the newest rows are `push`
failures, or there is no new row at all, the workflow file is invalid and
nothing ran -- that is exactly what happened for v4.7.0. See defect 3 in
the section 1 box for how to confirm and fix it.

`gh release create` with a *new* tag would fire both events at once. Push
the tag separately anyway: it keeps the PyPI publish and the docs publish
independently observable, so a failure in one is unambiguous.

### Confirm which repo `gh` is talking to

This clone has two remotes -- `origin` (`MattGyverLee/flexicon`) and
`upstream` (`cdfarrow/flexlibs`, the fork parent). With no default set,
`gh` prefers `upstream`, where these tags and issues do not exist. Run
once per clone:

```bash
gh repo set-default MattGyverLee/flexicon
```

---

## 6. If something goes wrong

**Build or publish job failed, nothing reached PyPI.** Delete the tag,
fix, re-tag. The tag is only a pointer until PyPI accepts the upload.

```bash
git tag -d v<version>
git push origin :refs/tags/v<version>
```

**PyPI already accepted the upload.** The version is spent permanently.
PyPI refuses re-uploads of a version even after deletion. Do not try to
reuse it -- yank the bad release via the PyPI web UI
(Manage -> Releases -> Yank) and cut the next patch.

A yanked version stays installable by exact pin but is skipped by
resolvers, which is the correct outcome for a broken release.

**Tag pushed to the wrong commit.** If PyPI has not yet accepted, delete
and re-push as above. If it has, the tag must stay where it is to match
the artifact; cut a new patch instead.

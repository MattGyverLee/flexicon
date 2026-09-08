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

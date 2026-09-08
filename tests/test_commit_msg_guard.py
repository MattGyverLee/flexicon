#
#   test_commit_msg_guard.py
#
#   Class: TestCommitMsgGuard
#          Coverage for the commit-msg auto-close guard in
#          .githooks/commit_msg_guard.py.
#
#   Platform: Python 3
#
#   Copyright 2025
#

"""
Tests for the commit-msg auto-close guard.

The guard exists because a GitHub close keyword in PROSE about an issue still
fires when the commit reaches the default branch. It has happened three times
in this repo (#242, #243, #250), twice against an explicit ruling that the
issue stay open.

The guard must satisfy two competing requirements, so both are pinned here:

  1. It must catch the hazard shapes -- negation, possessive, quotation.
  2. It must NOT disturb the genuine `closes #N` convention, which is used in
     100+ commits on main. A guard with false positives gets switched off.

The regression cases below are the real message lines from the incidents.
"""

import importlib.util
import pathlib

import pytest

GUARD_PATH = (pathlib.Path(__file__).resolve().parents[1]
              / ".githooks" / "commit_msg_guard.py")


def _load_guard():
    spec = importlib.util.spec_from_file_location("commit_msg_guard", GUARD_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def guard():
    if not GUARD_PATH.exists():
        pytest.skip("commit-msg guard not present")
    return _load_guard()


def _blocks(guard, message):
    return bool(guard.violations(guard.strip_noise(message)))


# The three messages that actually closed an issue in this repo, plus the two
# "does not close #N" bodies and the quoted directive found by backtesting.
HAZARDS = [
    pytest.param(
        "verbatim as a comment on flexicon#250. Do NOT close #250; do NOT edit its body,",
        "250", id="negation-250-real-incident"),
    pytest.param(
        "test(243): pin the fail-open branch; close #243's crew review (T9)",
        "243", id="possessive-243-real-incident"),
    pytest.param(
        "Fixes #242's P8 anomaly: now that Create/SetText/InsertAt preserve",
        "242", id="possessive-242-real-incident"),
    pytest.param(
        "records that B1 does not close #237 (needs B2 + a live B2t test).",
        "237", id="negation-237-in-prose"),
    pytest.param(
        "Closes #233, #234. Closes #235 as in-process-only. Does not close #237",
        "237", id="negation-237-after-genuine-footer"),
    pytest.param(
        'The earlier commit f3cc581 said "partially closes #151" but Delete still',
        "151", id="quoted-directive-151"),
]

# Real subject/footer lines from main that must keep working untouched.
GENUINE = [
    pytest.param("feat(msa): add feature-struct sync methods (closes #251)",
                 id="subject-parenthetical"),
    pytest.param("Closes #256.", id="footer-single"),
    pytest.param("Closes #233, #234, #235 (in-process-only scope).",
                 id="footer-multi-with-scope"),
    pytest.param("Closes MattGyverLee/flexlibs#4 #6 #7 #8. Two adjacent sites",
                 id="footer-qualified-repo"),
    pytest.param("fix(Lexicon): use lexDB.PublicationTypesOA not lp.Pubs (closes #218)",
                 id="negation-earlier-in-subject-close-in-parens"),
    pytest.param("fix(x): default wsHandle to vernacular WS, not analysis (closes #41)",
                 id="negation-before-parenthetical"),
    pytest.param("fix(x): correct Gloss read/write surface (closes #16)",
                 id="narration-word-before-parenthetical"),
    pytest.param("Headless ILcmUI (closes #238):", id="inline-parenthetical-in-body"),
]


class TestCommitMsgGuard:
    """The guard blocks hazard-shaped prose and leaves real closes alone."""

    @pytest.mark.parametrize("line,issue", HAZARDS)
    def test_hazard_shapes_are_blocked(self, guard, line, issue):
        found = guard.violations([line])
        assert found, "guard failed to flag a known hazard: %r" % line
        assert issue in {num for _, _, _, num, _ in found}

    @pytest.mark.parametrize("line", GENUINE)
    def test_genuine_close_convention_is_not_blocked(self, guard, line):
        assert not _blocks(guard, line), (
            "guard would reject the project's own close convention: %r" % line)

    def test_bare_issue_reference_without_keyword_is_allowed(self, guard):
        assert not _blocks(guard, "chore: note the #250 discussion and #242 outcome")

    def test_rephrasings_suggested_by_the_error_message_pass(self, guard):
        # The guard must not reject the fix it tells the author to apply.
        assert not _blocks(guard, "test(243): pin the branch; close the crew review for #243")
        assert not _blocks(guard, "docs: leave #250 OPEN while D4 is open")
        assert not _blocks(guard, "fix(x): fix the P8 anomaly reported in #242")

    def test_override_trailer_is_honoured(self, guard, tmp_path, monkeypatch):
        hazard = "docs: do NOT close #250 while D4 is open\n"
        assert _blocks(guard, hazard), "sanity: this body is hazard-shaped"

        msg = tmp_path / "COMMIT_EDITMSG"
        monkeypatch.delenv("FLEXICON_ALLOW_CLOSE_PROSE", raising=False)
        monkeypatch.setattr("sys.argv", ["guard", str(msg)])

        msg.write_text(hazard, encoding="utf-8")
        assert guard.main() == 1, "guard must reject the hazard without a trailer"

        msg.write_text(
            hazard + "\nClose-Keyword-Override: documenting the incident\n",
            encoding="utf-8")
        assert guard.main() == 0, "trailer must let the same message through"

    def test_env_override_is_honoured(self, guard, tmp_path, monkeypatch):
        msg = tmp_path / "COMMIT_EDITMSG"
        msg.write_text("docs: do NOT close #250 while D4 is open\n", encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["guard", str(msg)])
        monkeypatch.setenv("FLEXICON_ALLOW_CLOSE_PROSE", "1")
        assert guard.main() == 0

    def test_git_comment_lines_are_ignored(self, guard):
        # git strips these before committing, so they can never fire.
        assert not _blocks(guard, "chore: something\n\n# Conflicts:\n#\tdo NOT close #250\n")

    def test_verbose_diff_body_is_ignored(self, guard):
        message = ("chore: something\n\n"
                   "diff --git a/x b/x\n"
                   "+# do NOT close #250\n")
        assert not _blocks(guard, message)

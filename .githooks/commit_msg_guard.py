#
#   commit_msg_guard.py
#
#   Class: (script)
#          Rejects GitHub auto-close keywords that appear in PROSE about an
#          issue, while allowing the project's genuine `closes #N` footer
#          convention. Invoked by the commit-msg hook.
#
#   Platform: Python 3
#
#   Copyright 2025
#

"""
Guard against accidental GitHub issue auto-closure from commit messages.

GitHub fires on `<keyword> #N` wherever it appears in a commit message that
reaches the default branch -- it does not read intent. This repo has been
bitten three times (#242, #243, #250), every time by prose ABOUT an issue
rather than a real close directive:

    Do NOT close #250; do NOT edit its body   -> closed #250   (negation)
    close #243's crew review (T9)             -> closed #243   (possessive)
    Fixes #242's P8 anomaly                   -> closed #242   (possessive)

The keyword lies dormant on an unpushed or feature-branch commit and fires
when the commit reaches the default branch.

The legitimate convention -- `closes #N` in a footer or a subject
parenthetical -- is used in 100+ commits on main and is NOT touched. This
guard only blocks the hazard shapes: a negation, a possessive, a quotation,
or narration of a close that already happened.

Exit codes:
    0  no hazard found (or explicitly overridden)
    1  hazard found; the commit is rejected

Override, when the prose form is genuinely intended:
    add a trailer line `Close-Keyword-Override: <reason>`, or set
    FLEXICON_ALLOW_CLOSE_PROSE=1 in the environment.
"""

import os
import re
import sys

KEYWORD = r"clos(?:e|es|ed)|fix(?:|es|ed)|resolv(?:e|es|ed)"

# Keyword, optional colon, optional space, optional owner/repo, then #N.
FIRING = re.compile(
    r"\b(?P<kw>" + KEYWORD + r")\b[ \t]*:?[ \t]*"
    r"(?P<repo>(?:[\w.\-]+/)?[\w.\-]+)?#(?P<num>\d+)",
    re.IGNORECASE,
)

# A negation anywhere shortly before the keyword: the sentence says the issue
# must NOT be closed, which is exactly when GitHub closes it anyway.
NEGATORS = re.compile(
    r"\b(?:not|never|without|nor|no\s+longer|rather\s+than|instead\s+of|avoid"
    r"|do\s+not|does\s+not|did\s+not|will\s+not|must\s+not|should\s+not"
    r"|cannot|can\s?not)\b|n't\b",
    re.IGNORECASE,
)

# "close #243's crew review" -- possessive after the number reads as prose.
POSSESSIVE = re.compile(r"^'s\b", re.IGNORECASE)

# Narration of a close that already happened, or a hypothetical one.
NARRATION = re.compile(
    r"\b(?:was|were|has\s+been|have\s+been|already|accidentally|wrongly"
    r"|mistakenly|auto|auto-closed?|said|says|parsed|would|whether|reads?"
    r"|claimed|reported|records?)\b",
    re.IGNORECASE,
)

OVERRIDE_TRAILER = re.compile(r"^Close-Keyword-Override:\s*\S", re.IGNORECASE)

# How far back on the line to look for a negation / narration cue.
LOOKBEHIND = 45


def strip_noise(raw):
    """Drop comment lines, the scissors section, and any --verbose diff."""
    out = []
    for line in raw.splitlines():
        if line.startswith("# ------------------------ >8"):
            break
        if line.startswith("diff --git "):
            break
        if line.lstrip().startswith("#"):
            continue
        out.append(line)
    return out


def in_quotes(line, pos):
    """True if pos sits inside a paired quote on this line."""
    for q in ('"', "'"):
        if line.count(q) >= 2 and line.find(q) < pos < line.rfind(q):
            return True
    return False


def in_parens(line, pos):
    """True if pos sits inside a balanced (...) group on this line."""
    depth, opened = 0, []
    for i, ch in enumerate(line):
        if ch == "(":
            depth += 1
            opened.append(i)
        elif ch == ")" and depth:
            depth -= 1
            start = opened.pop()
            if start < pos < i:
                return True
    return False


def at_line_start(line, pos):
    """True if the match begins the line, ignoring leading bullets/brackets."""
    return not line[:pos].strip(" 	-*>[(#.")


def canonical_close_position(line, pos):
    """
    True where a close directive conventionally lives: inside a parenthetical
    ("feat(x): y (closes #N)") or opening the line ("Closes #N."). In those
    positions a `not` or `already` elsewhere on the line is almost always
    about something else, so the weaker cues are not applied there.
    """
    return in_parens(line, pos) or at_line_start(line, pos)


def classify(line, m):
    """Return a reason string if this match is hazard-shaped, else None."""
    before = line[max(0, m.start() - LOOKBEHIND):m.start()]
    after = line[m.end():]

    if POSSESSIVE.match(after):
        return "possessive: \"%s #%s's ...\" is prose, but still fires" % (
            m.group("kw"), m.group("num"))
    if in_quotes(line, m.start()):
        return "quoted: quoting a close directive still fires it"

    # Negation and narration are only meaningful when the keyword is embedded
    # in a sentence; in a canonical close position they are noise.
    if canonical_close_position(line, m.start()):
        return None

    if NEGATORS.search(before):
        return "negated: the sentence says NOT to close it; GitHub ignores that"
    if NARRATION.search(before):
        return "narration: describes a close that already happened or might"
    return None


def violations(lines):
    """Return [(lineno, line, keyword, issue, reason)] for hazard-shaped hits."""
    found = []
    for idx, line in enumerate(lines):
        for m in FIRING.finditer(line):
            reason = classify(line, m)
            if reason:
                found.append((idx + 1, line.strip(), m.group("kw"),
                              m.group("num"), reason))
    return found


def main():
    if os.environ.get("FLEXICON_ALLOW_CLOSE_PROSE") == "1":
        return 0

    with open(sys.argv[1], "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read()

    lines = strip_noise(raw)
    if any(OVERRIDE_TRAILER.match(ln.strip()) for ln in lines):
        return 0

    bad = violations(lines)
    if not bad:
        return 0

    issues = sorted({n for _, _, _, n, _ in bad}, key=int)
    sys.stderr.write(
        "\n[BLOCKED] commit-msg: auto-close keyword used in PROSE about an\n"
        "          issue. Pushed to the default branch, this would CLOSE: %s\n\n"
        % ", ".join("#" + n for n in issues)
    )
    for lineno, line, kw, num, reason in bad:
        shown = line if len(line) <= 92 else line[:89] + "..."
        sys.stderr.write("  line %-3d %s\n" % (lineno, shown))
        sys.stderr.write("           -> \"%s #%s\" fires here\n" % (kw, num))
        sys.stderr.write("              %s\n" % reason)

    sys.stderr.write(
        "\n  GitHub does not read intent. This exact shape has already closed\n"
        "  #242, #243 and #250 in this repo, twice against an explicit ruling\n"
        "  that the issue stay open.\n"
        "\n  Rephrase so the verb does not touch the number:\n"
        "    BAD   close #243's crew review (T9)\n"
        "    GOOD  close the crew review for #243\n"
        "    BAD   docs: do NOT close #250 while D4 is open\n"
        "    GOOD  docs: leave #250 OPEN while D4 is open\n"
        "    BAD   fix(x): Fixes #242's P8 anomaly\n"
        "    GOOD  fix(x): fix the P8 anomaly reported in #242\n"
        "\n  A genuine close is untouched by this guard: keep it as a footer\n"
        "  (\"Closes #N.\") or a subject parenthetical (\"feat(x): y (closes #N)\").\n"
        "\n  If the prose form really is intended, add a trailer:\n"
        "    Close-Keyword-Override: <why this should genuinely close it>\n\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

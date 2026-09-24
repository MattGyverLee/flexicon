#
#   test_issue230_semantic_domain_occurrences_ratchet.py
#
#   Offline ratchet for issue #230 gap 2: ICmSemanticDomain has no OccurrencesRS.
#   Prevents reintroducing the WfiWordform copy pattern removed in #352 live work.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SEMANTIC_DOMAIN_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Lexicon" / "SemanticDomainOperations.py"
)


def test_semantic_domain_operations_does_not_access_occurrences_rs():
    source = SEMANTIC_DOMAIN_OPS.read_text(encoding="utf-8")
    assert "OccurrencesRS" not in source, (
        "SemanticDomainOperations must not reference OccurrencesRS on "
        "ICmSemanticDomain (issue #230 gap 2; see specs/352-copyalternatives-audit)."
    )

#
#   test_issue293_gramcat_stray_docs_ratchet.py
#
#   Pins the hand-cleanup recipe for pre-#276 GramCat.Create strays
#   (issue #293) in docs/MIGRATION_GUIDE.md so the section cannot
#   silently shrink.
#
#   Platform: Python 3
#
#   Copyright 2026
#

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MIGRATION_GUIDE = _REPO_ROOT / "docs" / "MIGRATION_GUIDE.md"

# Each tuple: (human label, substring that must appear in the guide)
_REQUIRED_FRAGMENTS = (
    ("issue #293 reference", "Issue #293"),
    ("affected by GramCat.Create before #276", "before issue #276"),
    ("FLEx Features location", "Grammar > Features"),
    ("FLEx delete warning", "warns or blocks"),
    ("UI-only removal", "only through the FLEx UI"),
    ("no auto-migration", "none is planned"),
    ("forward POS.Create", "project.POS.Create(name, abbreviation)"),
    ("forward TypeCreate", "project.InflectionFeatures.TypeCreate"),
    ("domain ruling pointer", "domain-ruling.md"),
)


def test_migration_guide_contains_gramcat_stray_hand_cleanup_recipe():
    text = _MIGRATION_GUIDE.read_text(encoding="utf-8")
    missing = [label for label, frag in _REQUIRED_FRAGMENTS if frag not in text]
    assert not missing, (
        "docs/MIGRATION_GUIDE.md is missing required #293 hand-cleanup "
        f"fragments: {missing}"
    )

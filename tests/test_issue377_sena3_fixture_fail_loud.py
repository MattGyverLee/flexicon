#
#   test_issue377_sena3_fixture_fail_loud.py
#
#   Offline regression for issue #377: sena3_sandbox must route
#   OpenProject failures through _unavailable() so FLEXLIBS_REQUIRE_LIVE=1
#   fails loud like target_sandbox.
#
#   Platform: Python (no FieldWorks required)
#

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FLEX_PLUGIN = REPO_ROOT / "tests" / "flex_plugin.py"


def test_issue377_sena3_openproject_failure_uses_unavailable_gate():
    source = FLEX_PLUGIN.read_text(encoding="utf-8")
    marker = 'f"OpenProject rejected sandbox path {fwdata_path}: {exc}"'
    idx = source.index(marker)
    window = source[idx - 120 : idx + len(marker) + 40]

    assert "_unavailable(" in window
    assert "pytest.skip(" not in window, (
        "OpenProject failure in sena3_sandbox must call _unavailable(), "
        "not pytest.skip() (issue #377)"
    )

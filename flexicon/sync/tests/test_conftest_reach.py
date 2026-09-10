#
#   test_conftest_reach.py
#
#   Regression test for issue #307: the session-scoped autouse FLEx
#   initialization fixture must reach flexicon/sync/tests/, which sits
#   OUTSIDE the tests/ subtree where it used to be defined.
#
#   A conftest.py registers its fixtures only for its own directory
#   subtree. While initialize_flex_for_tests lived in tests/conftest.py, a
#   file- or directory-targeted run here initialized no FLEx at all -- so
#   these tests could fail with a confusing FLEx-not-initialized error or,
#   worse, appear to pass without ever exercising real FLEx behavior.
#
#   The fixture now lives in tests/flex_plugin.py, registered globally by
#   the repository-root conftest.py. This test pins that reach so the gap
#   cannot silently reopen.
#
#   Deliberately NOT marked requires_live_project: the point is that the
#   fixture RAN, which is equally true in mock mode. _LCM_MODE is left at
#   its "unknown" initial value if and only if the fixture never executed.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import tests.flex_plugin as flex_plugin


class TestFlexInitFixtureReach:
    """The global FLEx-init fixture reaches this directory."""

    def test_root_conftest_registers_the_flex_plugin(self, pytestconfig):
        assert pytestconfig.pluginmanager.hasplugin("tests.flex_plugin"), (
            "tests.flex_plugin is not registered. The repository-root "
            "conftest.py must declare pytest_plugins = (\"tests.flex_plugin\",); "
            "without it this directory gets no FLEx initialization (issue #307)."
        )

    def test_session_fixture_actually_ran(self):
        assert flex_plugin._LCM_MODE != "unknown", (
            "initialize_flex_for_tests never executed for a test in "
            "flexicon/sync/tests/. FLEx was not initialized, so any "
            "test here that opens a project is unverified (issue #307)."
        )

    def test_shared_fixtures_are_available_here(self, request):
        # A fixture defined in the plugin must be resolvable from this
        # subtree, not just from tests/.
        for name in ("initialize_flex_for_tests", "target_sandbox_path"):
            assert name in request.fixturenames or request._fixturemanager.getfixturedefs(
                name, request.node
            ), f"fixture {name!r} is not visible in flexicon/sync/tests/"

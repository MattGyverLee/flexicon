#
#   conftest.py
#
#   Repository-root pytest configuration.
#
#   Registers tests/flex_plugin.py -- the session-scoped autouse
#   `initialize_flex_for_tests` fixture, the shared mock/sandbox fixtures,
#   and the hooks that write tests/live_status.json -- as a global plugin.
#
#   A conftest.py registers its fixtures and hooks only for its own
#   directory subtree. When this machinery lived in tests/conftest.py,
#   flexicon/tests/ and flexicon/sync/tests/ sat OUTSIDE that subtree, so a
#   file- or directory-targeted invocation in either one initialized no
#   FLEx and wrote no evidence file. Those tests could fail with a
#   confusing FLEx-not-initialized error or, worse, appear to pass without
#   ever exercising real FLEx behavior. See issue #307.
#
#   `pytest_plugins` is only legal in the top-level conftest, which is why
#   this file is at the repository root rather than in the two test
#   directories that needed it -- pytest rejects the declaration outright in
#   a non-top-level conftest.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

pytest_plugins = ("tests.flex_plugin",)

# -*- coding: utf-8 -*-
#
# flexicon documentation build configuration file, created by
# sphinx-quickstart on Sat Feb 18 22:39:00 2012.
#
# This file is execfile()d with the current directory set to its containing dir.
#

import sys, os

# Add the path to the flexicon root for documenting the code with autodoc.
# (We need to use os.path.abspath to make the relative path absolute.)
sys.path.insert(0, os.path.abspath("..\\..\\"))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "flexicon"
author = "Matthew Lee"
# flexicon builds on Craig Farrow's flexlibs (https://github.com/cdfarrow/flexlibs),
# acknowledged here as the predecessor project.
copyright = "%Y, Matthew Lee. Based on flexlibs by Craig Farrow."


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Auto-doc the FLExProject code, and provide the source code, too.
# napoleon parses the Google-style docstrings (Args/Returns/Raises/Example)
# used throughout FLExProject; without it those sections are treated as raw
# reStructuredText and their indented continuation lines raise warnings.
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
]

# Render Google-style "Attributes:" sections as inline :ivar: field entries
# rather than standalone attribute directives. On the @dataclass models in
# flexicon.sync (Change, ValidationIssue, ...) the fields are ALSO documented
# from their annotations by autodoc; without this, each field gets two object
# descriptions ("duplicate object description" warnings).
napoleon_use_ivar = True

# autodoc imports every module it documents. `import flexicon` runs
# flexicon.code.FLExInit at import time, which calls
# FLExGlobals.InitialiseFWGlobals() -> a Windows-registry probe that raises
# "FieldWorks 9 not found" when FLEx is absent. That bootstrap runs real code,
# not just imports, so autodoc_mock_imports (clr/System/SIL/Microsoft) cannot
# satisfy it -- mocking the .NET namespaces still leaves the registry probe
# failing. The docs are therefore built against a live FieldWorks install
# (which also gives autodoc the real LCM signatures). Building on a machine
# without FieldWorks would require FLExInit to gain an import-time bypass.

# Document every member, including undocumented ones and inherited members,
# so the generated pages mirror the full public API surface.
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    # The package __init__ files re-export names from their submodules via
    # __all__ (e.g. flexicon.sync re-exports MatchStrategy from
    # flexicon.sync.match_strategies). Honouring __all__ would document those
    # names on BOTH the package page and the submodule page -> "duplicate
    # object description" and ambiguous-cross-reference warnings. Ignoring
    # __all__ makes autodoc select members by their defining module, so each
    # object is documented exactly once on its canonical submodule page.
    "ignore-module-all": True,
}

# Keep source order (definition order in the file) rather than alphabetical,
# which reads more naturally for the CRUD-grouped Operations classes.
autodoc_member_order = "bysource"

# The suffix of source filenames.
source_suffix = {".rst": "restructuredtext"}

# The master toctree document.
master_doc = "index"

# The default Pygments (syntax highlighting) style.
pygments_style = "sphinx"

# Show the method names in the TOC, but hide the full path.
toc_object_entries = True
toc_object_entries_show_parents = "hide"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.
# Pyramid is a clean theme with a contents pane on the left.
html_theme = "pyramid"

html_theme_options = {
    "sidebarwidth": 280,  # Wider to fit the method names (defaut=230)
}

# A general index (genindex.html) is useful now that the whole package is
# documented across many modules.
html_use_index = True

# No need for the reST sources.
html_copy_source = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
# html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
# html_show_copyright = True

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
copyright = "%Y, Craig Farrow"


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

# The suffix of source filenames.
source_suffix = {".rst": "restructuredtext"}

# The master toctree document.
master_doc = "flexicon"

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

# No need for an index (genindex.html) with the TOC in alphabetical order.
html_use_index = False

# No need for the reST sources.
html_copy_source = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
# html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
# html_show_copyright = True

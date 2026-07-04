The Sphinx configuration was created by:

    1. sphinx-apidoc -o <outputdir> <package-dir>
       i.e. sphinx-apidoc -o sphinx flexicon

    2. Editing the conf.py file to specify version, author, etc.
       Editing flexicon.rst to include only the FLExProject class

The documentation is built with:
    sphinx-build -b html docs/sphinx flexicon/docs/flexiconAPI
    (This is what make.bat does)

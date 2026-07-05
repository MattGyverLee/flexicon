@ECHO OFF
REM Simple build commands for flexicon

REM Build with the default Python version
set PYTHON=py

REM Check that the argument is a valid command, and do it. /I ignores case.
FOR %%C IN ("Init"
            "Test"
            "Clean"
            "Build"
            "Docs"
            "PublishDocs"
            "Publish") DO (
            IF /I "%1"=="%%~C" GOTO :Do%1
)
    
:Usage
    echo Usage:
    echo      make init         - Install the libraries for building
    echo      make test         - Run the unit tests
    echo      make clean        - Clean out build files
    echo      make build        - Build the project
    echo      make docs         - Build the Sphinx HTML docs only
    echo      make publishdocs  - Build the docs and deploy to GitHub Pages
    echo      make publish      - Publish the project to PyPI
    goto :End

:DoInit
    %PYTHON% -m pip install -r requirements.txt
    goto :End
    
:DoTest
    %PYTHON% -m pytest
    goto :End

:DoClean
    rmdir /s /q ".\build"
    rmdir /s /q ".\dist"
    rmdir /s /q ".\flexicon\docs"
    rmdir /s /q ".\docs\sphinx\api"
    rmdir /s /q ".\pyflexicon.egg-info"
    rmdir /s /q ".\flexicon.egg-info"
    rmdir /s /q ".\.pytest_cache"
    del /q ".\pytest_output.txt" 2>nul
    del /q ".\pytest_operations.txt" 2>nul
    del /q ".\test_run_output.txt" 2>nul
    goto :End
    
:DoBuild
    @REM Regenerate the per-module API stubs (whole package, excluding the
    @REM package's own tests/ and examples/), then build the HTML site.
    sphinx-apidoc -f -o docs/sphinx/api flexicon flexicon/tests flexicon/examples flexicon/sync/tests
    sphinx-build docs/sphinx flexicon/docs/flexiconAPI

    @REM Build the wheel with setuptools
    %PYTHON% -m build -w -nx
    
    @REM Check for package errors
    %PYTHON% -m twine check .\dist\*
    goto :End
    
:DoDocs
    @REM Build only the Sphinx HTML site (no wheel). Must run on a machine with
    @REM FieldWorks installed: `import flexicon` probes the FW registry at import
    @REM time and autodoc cannot mock that away (see docs/sphinx/conf.py).
    sphinx-apidoc -f -o docs/sphinx/api flexicon flexicon/tests flexicon/examples flexicon/sync/tests
    sphinx-build docs/sphinx flexicon/docs/flexiconAPI
    goto :End

:DoPublishDocs
    @REM Build the docs, then deploy the HTML to the gh-pages branch. -n adds
    @REM .nojekyll so Sphinx's _static/ dirs survive; -c writes the CNAME file
    @REM for the custom domain (else -f would wipe it each deploy); -p pushes;
    @REM -f overwrites. GitHub Pages serves gh-pages root at flexicon.langtech.cloud.
    call "%~f0" docs
    %PYTHON% -m ghp_import -n -c flexicon.langtech.cloud -p -f -m "docs: publish flexicon Sphinx API to GitHub Pages" flexicon/docs/flexiconAPI
    goto :End

:DoPublish
    echo Publishing wheel to PyPI
    %PYTHON% -m twine upload .\dist\pyflexicon*
    goto :End


:End

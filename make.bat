@ECHO OFF
REM Simple build commands for flexicon

REM Build with the default Python version
set PYTHON=py

REM Check that the argument is a valid command, and do it. /I ignores case.
FOR %%C IN ("Init"
            "Test"
            "Clean"
            "Build"
            "Publish") DO (
            IF /I "%1"=="%%~C" GOTO :Do%1
)
    
:Usage
    echo Usage:
    echo      make init         - Install the libraries for building
    echo      make test         - Run the unit tests
    echo      make clean        - Clean out build files
    echo      make build        - Build the project
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
    
:DoPublish
    echo Publishing wheel to PyPI
    %PYTHON% -m twine upload .\dist\pyflexicon*
    goto :End


:End

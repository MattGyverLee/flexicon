#
#   test_wfianalysis_agent_import.py
#
#   Regression coverage for WfiAnalysisOperations approval-path imports.
#

import ast
from pathlib import Path


def test_wfianalysis_approval_imports_agent_operations_from_lists_package():
    source = Path("flexicon/code/TextsWords/WfiAnalysisOperations.py").read_text()
    tree = ast.parse(source)

    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "Lists.AgentOperations"
        and node.level == 2
        and any(alias.name == "AgentOperations" for alias in node.names)
    ]

    assert imports, "SetApprovalStatus should import AgentOperations from code.Lists"
    assert "from .AgentOperations import AgentOperations" not in source

### Problem Statement

Write a Python function to perform a guarded deep-duplicate write probe on the 'Target' FLEx project, ensuring conservation of semantic domains and Question values.

### Key Requirements

- Accessor name: `project.SemanticDomains` (from `FLExProject.py`).
- Use `TEST_` prefix for temporary objects to ensure cleanup.
- Capture pre/post values using `report.Info` for evidence.
- Leverage `Lexicon/SemanticDomainOperations.py` for existing method signatures and tests.
- Use the canonical `test_target_live_smoke.py` as a template for the live-test structure.
- Read `C:\Github\flexicon\flexicon\code\FLExProject.py` and `C:\Github\flexicon\flexicon\code\Lexicon\SemanticDomainOperations.py`.

### Objectives

1. Implement a function that creates a temporary semantic domain in the target project.
2. Duplicate this domain with a deep probe.
3. Verify that the copied object maintains all properties, especially the 'Questions' sequence, which is of type `ILcmOwningSequence`.
4. Ensure the original domain remains unchanged.
5. Clean up the temporary domain after the test.

### Verification

- Use the `target_project` fixture to perform all operations.
- Write the function in `test_target_live_smoke.py`.
- Include evidence from the LCM query results, specifically demonstrating that the Questions property is properly preserved in the deep duplicate.

### Relevant Files

- `C:\Github\flexicon\flexicon\code\FLExProject.py`: Defines the `FLExProject` class and its accessor methods.
- `C:\Github\flexicon\flexicon\code\Lexicon\SemanticDomainOperations.py`: Contains core logic for manipulating semantic domains, including the `Duplicate` and `Delete` methods, which are critical for the test strategy.
- `C:\Github\flexicon\tests\operations\test_target_live_smoke.py`: Provides the canonical template for live-test structure with proper fixture handling and cleanup protocols.
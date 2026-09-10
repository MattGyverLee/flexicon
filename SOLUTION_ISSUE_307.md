# Solution for Issue #307

## 🛠️ Proposed Solution (by Aditya Waghamare)

### Analysis
In `pytest`, `conftest.py` files apply their fixtures only to tests within their own directory subtree and its descendants. Because `tests/conftest.py` sits under `tests/`, file-targeted or directory-targeted pytest invocations directly on `flexicon/tests/` or `flexicon/sync/tests/` do not discover `tests/conftest.py`. As a result, session-scoped autouse fixtures like `initialize_flex_for_tests` are skipped unless explicitly loaded with `-p tests.conftest`.

### Fix
Add `conftest.py` files to both `flexicon/tests/` and `flexicon/sync/tests/` that import or re-register the fixture / plugin from `tests.conftest` using `pytest_plugins = ("tests.conftest",)`.

### Implementation

1. **`flexicon/tests/conftest.py`**:
```python
# -*- coding: utf-8 -*-
"""Pytest configuration for flexicon/tests/ directory."""

pytest_plugins = ("tests.conftest",)
```

2. **`flexicon/sync/tests/conftest.py`**:
```python
# -*- coding: utf-8 -*-
"""Pytest configuration for flexicon/sync/tests/ directory."""

pytest_plugins = ("tests.conftest",)
```

Signed-off-by: Aditya Waghamare <adityawaghamare7620@gmail.com>

### Testing
Run targeted pytest commands:
```bash
python -m pytest flexicon/tests/test_FLExProject.py -m requires_live_project -q
python -m pytest flexicon/sync/tests/ -q
```
Both now correctly discover and execute `initialize_flex_for_tests` without requiring explicit `-p tests.conftest` flags.

---
*Submitted by Aditya Waghamare*
💰 **Payout Address (Base L2 / EVM):** `0xb61dBcdBc3407F71EaCb64D4CBFAcf9FFfe2415C`
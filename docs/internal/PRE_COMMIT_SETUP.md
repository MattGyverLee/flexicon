# Pre-commit Hooks Setup

This project uses **pre-commit hooks** to automatically check code before commits, preventing bugs like duplicate decorators.

## Installation

1. **Install pre-commit framework:**
   ```bash
   pip install pre-commit
   ```

2. **Install the git hooks:**
   ```bash
   pre-commit install
   ```

3. **Verify installation:**
   ```bash
   pre-commit run --all-files
   ```

## What Gets Checked

The hooks run **automatically before each commit** and check for:

### Custom Checks
- **Duplicate `@OperationsMethod` decorators** - Prevents `'OperationsMethod' object is not callable'` errors
  - Detects consecutive duplicate decorators on operation methods
  - Blocks commits with this issue

### Code Quality
- **Black formatting** - Consistent Python code style
- **Flake8 linting** - Code quality issues, unused imports, complexity warnings
- **Mixed line endings** - Enforces consistent line endings

### Security
- **Detect secrets** - Prevents committing API keys, credentials, passwords
- **Trailing whitespace** - Removes accidental whitespace

### General
- **JSON/YAML validation** - Ensures config files are valid
- **Merge conflicts** - Prevents committing unresolved conflicts

## Usage

### Automatic (Default)
Hooks run **before each commit** — if checks fail, the commit is blocked:

```bash
git add .
git commit -m "Your message"
# Hooks run automatically here
```

### Manual Runs

Check all files in the project:
```bash
pre-commit run --all-files
```

Check only specific hook:
```bash
pre-commit run check-duplicate-decorators
```

Check only files in a directory:
```bash
pre-commit run --files flexlibs2/code/Grammar/*.py
```

### Bypass (Not Recommended)

To skip hooks and commit anyway (use with caution):
```bash
git commit --no-verify -m "Your message"
```

## Troubleshooting

### Hook fails but code looks fine

**Formatter changed my code:**
- Black and Flake8 may auto-fix formatting issues
- Check `git diff` to see changes
- Review and re-stage: `git add .` and `git commit` again

**Decorator check fails:**
- Look for consecutive `@OperationsMethod` decorators
- Keep only one per method (unless intentionally stacking with `@wrap_enumerable`)
- Example fix:
  ```python
  # Before (wrong)
  @OperationsMethod
  @OperationsMethod
  def GetAll(self):

  # After (correct)
  @OperationsMethod
  def GetAll(self):
  ```

### Uninstall hooks

If you need to disable pre-commit:
```bash
pre-commit uninstall
```

To re-enable:
```bash
pre-commit install
```

## Adding New Hooks

To add more checks:

1. Edit `.pre-commit-config.yaml`
2. Run `pre-commit install`
3. Test with `pre-commit run --all-files`

## Related Files

- `.pre-commit-config.yaml` - Hook configuration
- `scripts/check_decorators.py` - Custom decorator checking script
- This file: `docs/internal/PRE_COMMIT_SETUP.md`

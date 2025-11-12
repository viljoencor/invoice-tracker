# Scripts

This directory contains utility scripts for development and operations.

## Available Scripts

### `run-checks.py`

Runs all quality checks in sequence:
- Linting (Ruff)
- Format checking (Ruff)
- Type checking (MyPy)
- Security scanning (Bandit)
- Tests with coverage

**Usage**:
```bash
python scripts/run-checks.py
```

This is useful as a pre-commit hook or before pushing code.

## Setting Up Pre-Commit Hook

To automatically run checks before each commit:

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
python scripts/run-checks.py
EOF

# Make it executable
chmod +x .git/hooks/pre-commit
```

Now quality checks will run automatically before each commit!

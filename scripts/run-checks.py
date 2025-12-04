#!/usr/bin/env python3
"""
Quick test runner script for Invoice Tracker backend.
Runs quality checks and tests in sequence.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str, cwd: Path = None) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True,
            cwd=cwd
        )
        print(f"{description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{description} - FAILED")
        return False


def main():
    """Run all quality checks and tests."""
    print("Invoice Tracker - Quality Check Runner")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent / "apps" / "backend"
    print(f"Working directory: {backend_dir}\n")
    
    checks = [
        (["uv", "run", "ruff", "check", "app", "tests"], "Linting (Ruff)", backend_dir),
        (["uv", "run", "ruff", "format", "--check", "app", "tests"], "Format Check (Ruff)", backend_dir),
        (["uv", "run", "mypy", "app"], "Type Checking (MyPy)", backend_dir),
        (["uv", "run", "bandit", "-r", "app", "-ll"], "Security Scan (Bandit)", backend_dir),
        (["uv", "run", "pytest", "--cov", "--cov-report=term-missing"], "Tests with Coverage", backend_dir),
    ]
    
    results = []
    
    for cmd, description, cwd in checks:
        success = run_command(cmd, description, cwd)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for description, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status} - {description}")
    
    # Exit code
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print(f"\n All checks passed! Ready to commit.")
        sys.exit(0)
    else:
        print(f"\n Some checks failed. Please fix issues before committing.")
        sys.exit(1)


if __name__ == "__main__":
    main()

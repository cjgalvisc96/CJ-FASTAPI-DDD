"""Enforce the architecture contracts (import-linter) as a test."""

from __future__ import annotations

import subprocess
import sys


def test_import_linter_contracts_hold() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "importlinter.cli", "lint"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

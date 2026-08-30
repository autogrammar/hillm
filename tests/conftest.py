"""Bootstrap dev install for clean checkouts (coding-agent worktrees)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VENV_BIN = ROOT / ".venv" / "bin"
HILLM_CLI = VENV_BIN / "hillm"


def _ensure_dev_install() -> None:
    if HILLM_CLI.is_file():
        return
    subprocess.run(
        [sys.executable, "-m", "venv", str(ROOT / ".venv")],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["bash", "packages/install-dev.sh"],
        cwd=ROOT,
        check=True,
    )


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_project_env() -> None:
    _ensure_dev_install()
    path = os.environ.get("PATH", os.defpath)
    os.environ["PATH"] = f"{VENV_BIN}{os.pathsep}{path}"
    os.environ.setdefault("HILLM_DRY_RUN", "1")

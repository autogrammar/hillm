"""Bootstrap dev install for clean checkouts (coding-agent worktrees)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VENV_BIN = ROOT / ".venv" / "bin"
REQUIRED_CLIS = ("hillm", "dsl2hillm", "uri2hillm", "nlp2hillm", "cli2hillm")


def _dev_install_complete() -> bool:
    return all((VENV_BIN / cli).is_file() for cli in REQUIRED_CLIS)


def _ensure_dev_install() -> None:
    if _dev_install_complete():
        return
    if not (ROOT / ".venv").is_dir():
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
    if not _dev_install_complete():
        missing = [cli for cli in REQUIRED_CLIS if not (VENV_BIN / cli).is_file()]
        raise RuntimeError(f"dev install incomplete; missing CLIs: {missing}")


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_project_env() -> None:
    _ensure_dev_install()
    path = os.environ.get("PATH", os.defpath)
    os.environ["PATH"] = f"{VENV_BIN}{os.pathsep}{path}"
    os.environ.setdefault("HILLM_DRY_RUN", "1")

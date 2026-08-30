"""Run examples/**/*.sh smoke scripts."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"

CORE_SCRIPTS = [
    "cli/devices.sh",
    "cli/scan.sh",
    "cli/read-dry-run.sh",
    "cli/write-dry-run.sh",
    "cli/status-ecosystem.sh",
    "cli/status-mouse-dry-run.sh",
    "cli/dsl-health.sh",
    "dsl/run-smoke.sh",
    "dsl/read-sensor-temp.sh",
    "dsl/devices-usb.sh",
    "control-layer/uri-dispatch.sh",
    "control-layer/uri-shorthand-read.sh",
    "control-layer/uri-decode-sensor.sh",
    "control-layer/nlp-to-dsl.sh",
    "control-layer/nlp-mouse-port.sh",
    "control-layer/dsl-live-policy.sh",
    "control-layer/cli-exec.sh",
    "nlp2hillm/to-dsl-temperature.sh",
    "nlp2hillm/to-dsl-mouse.sh",
    "nlp2hillm/to-dsl-mouse-port-pl.sh",
    "nlp2hillm/to-dsl-mouse-status-en.sh",
    "nlp2hillm/to-dsl-camera.sh",
    "nlp2hillm/to-dsl-modbus-connect.sh",
    "nlp2hillm/to-dsl-list-usb.sh",
    "nlp2hillm/to-dsl-health.sh",
    "nlp2hillm/apply-read-dry-run.sh",
    "nlp2hillm/apply-env-dry-run.sh",
    "nlp2hillm/apply-connect-modbus.sh",
    "nlp2hillm/apply-status-mouse-dry-run.sh",
    "nlp2hillm/apply-status-mouse-live.sh",
    "nlp2hillm/apply-verbose-rules.sh",
    "devices/display/status.sh",
    "devices/camera/capture-dry-run.sh",
    "devices/audio/status.sh",
    "devices/usb/list.sh",
    "devices/serial/read-dry-run.sh",
    "devices/modbus/read-dry-run.sh",
    "devices/input/mouse-status-live.sh",
    "devices/sensor/temp-read-dry-run.sh",
    "devices/sensor/temp-resolve-address.sh",
]

# Scripts that perform a live serial read and therefore need the optional
# `serial` extra (pyserial). Skipped when it isn't installed so the suite stays
# green on hosts without the serial transport stack.
SERIAL_SCRIPTS = [
    "nlp2hillm/apply-temperature-live.sh",
    "nlp2hillm/check-serial-env.sh",
    "devices/sensor/temp-status-live.sh",
]

NLP2URI_SCRIPTS = [
    "nlp2uri/compile-uri.sh",
    "nlp2uri/run-uri.sh",
]


def _run_script(rel: str) -> subprocess.CompletedProcess[str]:
    script = EXAMPLES / rel
    assert script.is_file(), f"missing example: {rel}"
    env = os.environ.copy()
    venv_bin = ROOT / ".venv" / "bin"
    if venv_bin.is_dir():
        env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', os.defpath)}"
    env.setdefault("HILLM_DRY_RUN", "1")
    return subprocess.run(
        ["bash", str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env=env,
    )


@pytest.mark.parametrize("rel", CORE_SCRIPTS)
def test_example_script(rel: str) -> None:
    proc = _run_script(rel)
    assert proc.returncode == 0, f"{rel} failed:\n{proc.stdout}\n{proc.stderr}"


@pytest.mark.parametrize("rel", SERIAL_SCRIPTS)
def test_serial_example_script(rel: str) -> None:
    pytest.importorskip("serial", reason="serial extra (pyserial) not installed")
    proc = _run_script(rel)
    assert proc.returncode == 0, f"{rel} failed:\n{proc.stdout}\n{proc.stderr}"


@pytest.mark.parametrize("rel", NLP2URI_SCRIPTS)
def test_nlp2uri_example_script(rel: str) -> None:
    pytest.importorskip("nlp2uri")
    pytest.importorskip("uri2hillm")
    proc = _run_script(rel)
    assert proc.returncode == 0, f"{rel} failed:\n{proc.stdout}\n{proc.stderr}"


def test_run_all_dry_run() -> None:
    # run-all-dry-run.sh includes live serial scripts; needs the serial extra.
    pytest.importorskip("serial", reason="serial extra (pyserial) not installed")
    proc = subprocess.run(
        ["bash", str(EXAMPLES / "run-all-dry-run.sh")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr

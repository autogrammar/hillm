"""Keep verbose diagnostics separate from command output and execution policy."""

import importlib.util
import json
from types import SimpleNamespace

import pytest
from nlp2hillm import cli

import hillm


@pytest.fixture(autouse=True)
def no_environment_bootstrap(monkeypatch):
    monkeypatch.setattr(cli, "bootstrap_project_env", lambda: None)


@pytest.mark.parametrize(
    "backend, model, label",
    [
        ("rules", None, "rules"),
        ("llm", None, "llm (openrouter/z-ai/glm-5.2)"),
        ("llm", "custom/model", "llm (custom/model)"),
    ],
)
@pytest.mark.parametrize("device", ["known", "unknown", "absent"])
@pytest.mark.parametrize("paths_present", [True, False])
def test_verbose_mapping_output(monkeypatch, capsys, backend, model, label, device, paths_present):
    line = "HEALTH" if device == "absent" else "READ DEVICE sensor-temp"
    monkeypatch.setattr(cli, "to_dsl_with_backend", lambda *a, **kw: (line, backend))
    if model is None:
        monkeypatch.delenv("LLM_MODEL", raising=False)
    else:
        monkeypatch.setenv("LLM_MODEL", model)
    spec = SimpleNamespace(id="sensor-temp", resolve_address=lambda: "/dev/test")
    monkeypatch.setattr(
        cli, "get_device_spec", lambda device_id: spec if device == "known" else None
    )
    monkeypatch.setattr(
        hillm, "__file__", "/installed/hillm/__init__.py" if paths_present else None
    )
    original_find_spec = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name, *a, **kw: (
            (SimpleNamespace(origin="/installed/nlp2hillm/__init__.py") if paths_present else None)
            if name == "nlp2hillm"
            else original_find_spec(name, *a, **kw)
        ),
    )

    assert cli.main(["read temperature", "--verbose"]) == 0
    captured = capsys.readouterr()
    assert captured.out == line + "\n"
    expected = [f"# mapped via: {label}"]
    if device == "known":
        expected.append("# device: sensor-temp → address '/dev/test'")
    expected.append("# hillm: /installed/hillm" if paths_present else "# hillm: ")
    if paths_present:
        expected.append("# nlp2hillm: /installed/nlp2hillm")
    assert captured.err == "\n".join(expected) + "\n"


@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.parametrize("ok", [False, True])
@pytest.mark.parametrize(
    "flags, dry_run", [([], True), (["--live"], False), (["--live", "--dry-run"], True)]
)
def test_apply_output_and_policy(monkeypatch, capsys, verbose, ok, flags, dry_run):
    calls = []
    monkeypatch.setattr(cli, "to_dsl_with_backend", lambda *a, **kw: ("HEALTH", "rules"))

    def policy(line, **kwargs):
        calls.append((line, kwargs))
        return "adjusted command"

    def dispatch(line):
        assert line == "adjusted command"
        return SimpleNamespace(ok=ok, to_dict=lambda: {"ok": ok})

    monkeypatch.setattr(cli, "apply_execution_policy", policy)
    monkeypatch.setattr(cli, "dispatch", dispatch)
    args = ["health", "--apply", *flags, *(["--verbose"] if verbose else [])]
    assert cli.main(args) == (0 if ok else 1)
    captured = capsys.readouterr()
    assert json.loads(captured.out) == ({"ok": ok, "mapper": "rules"} if verbose else {"ok": ok})
    assert bool(captured.err) is verbose
    assert calls == [("HEALTH", {"live": "--live" in flags, "dry_run": dry_run})]

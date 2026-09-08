"""Preserve URI CLI execution flags and explicit/shorthand output contracts."""

import json
from types import SimpleNamespace

import pytest
from uri2hillm import cli


@pytest.fixture(autouse=True)
def no_environment_bootstrap(monkeypatch):
    monkeypatch.setattr(cli, "bootstrap_project_env", lambda: None)


@pytest.mark.parametrize("prefix", [[], ["run"]])
@pytest.mark.parametrize(
    "flags, live, dry_run",
    [
        ([], False, True),
        (["--live"], True, False),
        (["--dry-run"], False, True),
        (["--live", "--dry-run"], True, True),
    ],
)
@pytest.mark.parametrize("filename", ["", "commands.dsl"])
def test_execution_arguments(monkeypatch, capsys, prefix, flags, live, dry_run, filename):
    calls = []

    def normalize(target, *, default_file):
        calls.append(("normalize", target, default_file))
        return "hillm://normalized"

    def run(uri, **kwargs):
        calls.append(("run", uri, kwargs))
        return SimpleNamespace(ok=True, output="done", error="", to_dict=lambda: {"ok": True})

    monkeypatch.setattr(cli, "normalize_uri_input", normalize)
    monkeypatch.setattr(cli, "run_uri", run)
    argv = [*prefix, "READ", "DEVICE", "sensor-temp", *flags, "--file", filename]
    original = list(argv)
    assert cli.main(argv) == 0
    assert argv == original
    assert calls == [
        ("normalize", "READ DEVICE sensor-temp", filename or None),
        (
            "run",
            "hillm://normalized",
            {
                "default_file": filename or None,
                "live": live,
                "dry_run": dry_run,
            },
        ),
    ]
    captured = capsys.readouterr()
    assert not captured.err
    if prefix:
        assert captured.out == "done\n"
    else:
        assert json.loads(captured.out) == {"ok": True}


@pytest.mark.parametrize(
    "prefix, as_json", [([], True), (["run"], False), (["run", "--json"], True)]
)
@pytest.mark.parametrize(
    "ok, output, error", [(True, "done", ""), (False, "", "failed"), (False, "partial", "failed")]
)
def test_output_and_exit_status(monkeypatch, capsys, prefix, as_json, ok, output, error):
    payload = {"ok": ok, "output": output, "error": error}
    monkeypatch.setattr(
        cli,
        "run_uri",
        lambda *a, **kw: SimpleNamespace(
            ok=ok, output=output, error=error, to_dict=lambda: payload
        ),
    )
    assert cli.main([*prefix, "HEALTH"]) == (0 if ok else 1)
    captured = capsys.readouterr()
    assert not captured.err
    if as_json:
        assert json.loads(captured.out) == payload
    else:
        assert captured.out == (output or error) + "\n"


@pytest.mark.parametrize("argv", [["HEALTH", "--json"], ["decode", "HEALTH", "--live"], ["run"]])
def test_mode_specific_argument_rejection(argv):
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    assert exc.value.code == 2

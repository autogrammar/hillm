import pytest


def test_live_hardware_access_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp2hillm.server import _guard_command

    monkeypatch.delenv("HILLM_MCP_ALLOW_EXECUTE", raising=False)
    for command in (
        "READ DEVICE sensor",
        "STATUS DEVICE sensor",
        "WRITE DEVICE relay VALUE 1",
        "ACTUATE DEVICE relay ACTION run",
    ):
        with pytest.raises(PermissionError, match="HILLM_MCP_ALLOW_EXECUTE"):
            _guard_command(command)


def test_dry_run_and_explicit_hardware_access_are_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from mcp2hillm.server import _guard_command

    monkeypatch.delenv("HILLM_MCP_ALLOW_EXECUTE", raising=False)
    _guard_command("WRITE DEVICE relay VALUE 1 DRY_RUN true")
    monkeypatch.setenv("HILLM_MCP_ALLOW_EXECUTE", "on")
    _guard_command("WRITE DEVICE relay VALUE 1")


def test_non_hardware_queries_remain_available(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp2hillm.server import _guard_command

    monkeypatch.delenv("HILLM_MCP_ALLOW_EXECUTE", raising=False)
    _guard_command("HEALTH")
    _guard_command("DEVICES")

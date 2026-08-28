from __future__ import annotations

import json
import os
from typing import Any

from dsl2hillm import dispatch
from mcp.server.fastmcp import FastMCP
from nlp2hillm.to_dsl import to_dsl

mcp = FastMCP("hillm")

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_HARDWARE_VERBS = frozenset(
    {"READ", "STATUS", "WRITE", "ACTUATE", "CONNECT", "DISCONNECT", "EXECUTE"}
)


def _enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUE_VALUES


def _guard_payload(payload: dict[str, Any]) -> None:
    verb = str(payload.get("verb", "")).upper()
    live_hardware_access = verb in _HARDWARE_VERBS and not bool(payload.get("dry_run", False))
    if live_hardware_access and not _enabled("HILLM_MCP_ALLOW_EXECUTE"):
        raise PermissionError(
            "live hardware access through MCP is disabled; "
            "use DRY_RUN true or set HILLM_MCP_ALLOW_EXECUTE=1"
        )


def _guard_command(command: str) -> None:
    from dsl2hillm.codec import parse_text

    payload = parse_text(command)
    if payload:
        _guard_payload(payload)


@mcp.tool()
def hillm_run_dsl(line: str) -> str:
    """Execute a dsl2hillm command line."""
    _guard_command(line)
    return json.dumps(dispatch(line).to_dict(), indent=2)


@mcp.tool()
def hillm_to_dsl(prompt: str) -> str:
    """Map natural language to dsl2hillm without executing."""
    return to_dsl(prompt)


@mcp.tool()
def hillm_run_command(command: str) -> str:
    """Alias for hillm_run_dsl."""
    return hillm_run_dsl(command)

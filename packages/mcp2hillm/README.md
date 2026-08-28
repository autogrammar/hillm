# mcp2hillm

MCP server exposing HILLM tools to IDE agents.

## Tools

| Tool | Description |
|------|-------------|
| `hillm_run_dsl` | Execute a dsl2hillm line |
| `hillm_to_dsl` | NL → DSL via nlp2hillm |
| `hillm_run_command` | Alias for `hillm_run_dsl` |

## Run

```bash
mcp2hillm stdio
```

Configure in your MCP client JSON (Cursor, Windsurf, …) pointing at `mcp2hillm`.

`hillm_run_dsl` uses `dispatch()` which auto-loads `.env`. Live device reads,
status checks, writes, actuation, connection changes, and execution are disabled
over MCP by default. Include `DRY_RUN true` for a safe preview, or explicitly set
`HILLM_MCP_ALLOW_EXECUTE=1` to allow live hardware access.

**See also:** [Control layer](../README.md) · [docs/control-layer.md](../../docs/control-layer.md)

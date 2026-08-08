# nlp2hillm

Natural language → `dsl2hillm` command line. Translates Polish and English hardware prompts into HILLM DSL, optionally executes them via `dsl2hillm.dispatch`.

## Two phases

| Phase | Command | Output |
| --- | --- | --- |
| **Map** | `nlp2hillm "prompt"` | One DSL line on stdout |
| **Execute** | `nlp2hillm "prompt" --apply` | JSON result from `dsl2hillm` |

`--apply` defaults to **dry-run** (simulated hardware). Use `--live` for real transports.

```bash
# 1) Map only — no hardware access
nlp2hillm "read temperature from serial"
# → READ DEVICE sensor-temp REGISTER temperature

# 2) Execute dry-run (safe default)
nlp2hillm "read temperature from serial" --apply
# → {"ok": true, "data": {"value": "dry:temperature", "backend": "dry_run", ...}}

# 3) Execute on real hardware
nlp2hillm "what port is the mouse on" --apply --live
# → {"ok": true, "data": {"value": ["usb-...-event-mouse", ...], "backend": "input", ...}}
```

## Backends

| Backend | When | Requires |
| --- | --- | --- |
| **Rules** | `--no-llm`, or clear keyword match | — |
| **OpenRouter LLM** | ambiguous prompt + `OPENROUTER_API_KEY` in `.env` | `pip install nlp2hillm[llm]` |

Priority:

1. `--no-llm` → always rules
2. `--use-llm` → always LLM (errors if LLM fails)
3. Default with API key → rules for clear patterns, LLM for ambiguous
4. Default without API key → rules only

Use `-v` / `--verbose` to print `# mapped via: rules` or `# mapped via: llm (model)` on stderr.

## CLI flags

| Flag | Description |
| --- | --- |
| `--apply` | Execute mapped DSL via `dsl2hillm` |
| `--live` | Real hardware on `--apply` (default is dry-run) |
| `--dry-run` | Force dry-run on `--apply` |
| `--no-llm` | Rule-based mapper only (deterministic, CI-friendly) |
| `--use-llm` | Force OpenRouter LLM mapping |
| `-v`, `--verbose` | Show mapping backend on stderr; add `mapper` to JSON on `--apply` |

## Environment (`.env`)

Auto-loaded from project root by `hillm.project_env.bootstrap_project_env()`:

```bash
# LLM (optional)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_APP_NAME=hillm
OPENROUTER_APP_URL=https://github.com/semcod/hillm
LLM_MODEL=openrouter/z-ai/glm-5.2

# Execution policy
HILLM_DRY_RUN=1                    # force dry-run transport globally

# Per-device address overrides (device id with - → _)
HILLM_SENSOR_TEMP_ADDRESS=/dev/ttyACM0
HILLM_MODBUS_HOST=127.0.0.1
HILLM_MQTT_URL=mqtt://127.0.0.1:1883
```

The LLM response is governed by the packaged `DslLineResponse` v1 bundle:
GBNF, Protobuf, JSON Schema and a manifest naming the runtime boundary. The
same schema is sent through LiteLLM and validated locally before the existing
`dsl2hillm` hardware grammar parser. Prose, unknown verbs, extra fields and
version drift fail closed. OpenRouter App attribution uses
`OPENROUTER_APP_NAME` with project-folder fallback.

## Mapping reference

### Verbs (rules)

| NL keywords (EN / PL) | DSL verb |
| --- | --- |
| `read`, `odczytaj`, `pobierz` | `READ` |
| `write`, `zapisz`, `ustaw` | `WRITE` |
| `connect`, `połącz`, `polacz` | `CONNECT` |
| `capture`, `snapshot`, `actuate`, … | `ACTUATE` |
| `status`, `stan`, `port`, `podłącz`, `na jakim porcie`, … | `STATUS` |
| `HEALTH`, `DEVICES`, `ORIENT`, `ACTIONS` | passthrough |
| `jakie` + `usb` / `urządzenia` | `DEVICES CATEGORY usb` |

### Devices (via `hillm.resolve`)

| Input hint | Device id |
| --- | --- |
| `temperature` / `temp` + `serial` | `sensor-temp` |
| `mouse` / `mysz` / `myszka` | `mouse-default` |
| `mouse` over `usb` | `mouse-default` (preferred over generic `usb-hub`) |
| `camera` / `webcam` | `camera-usb` |
| `modbus` | `modbus-rtu` |
| `usb` alone | `usb-hub` |
| `serial` alone | `serial-ttyacm0` or `serial-ttyusb0` (first existing path) |

### Example prompts

| Prompt | Mapped DSL |
| --- | --- |
| `read temperature from serial` | `READ DEVICE sensor-temp REGISTER temperature` |
| `na jakim porcie jest podłączona myszka?` | `STATUS DEVICE mouse-default` |
| `read usb port for mouse` | `READ DEVICE mouse-default` |
| `capture image from camera` | `ACTUATE DEVICE camera-usb ACTION capture` |
| `connect modbus device` | `CONNECT DEVICE modbus-rtu` |
| `jakie urządzenia usb są podłączone` | `DEVICES CATEGORY usb` |

## Install

```bash
# workspace (recommended)
cd hillm
uv sync --extra dev
bash packages/install-dev.sh

# LLM backend
uv sync --extra dev
pip install -e "packages/nlp2hillm[llm]"

# serial transport (for live temperature reads)
uv sync --extra serial
```

## Examples

Runnable scripts in [examples/nlp2hillm/](../../examples/nlp2hillm/):

```bash
# Mapping only (--no-llm for CI determinism)
bash examples/nlp2hillm/to-dsl-temperature.sh
bash examples/nlp2hillm/to-dsl-mouse-port-pl.sh
bash examples/nlp2hillm/to-dsl-list-usb.sh

# Dry-run execution
bash examples/nlp2hillm/apply-read-dry-run.sh
bash examples/nlp2hillm/apply-status-mouse-dry-run.sh

# Live hardware (skip gracefully when port/input missing)
bash examples/nlp2hillm/apply-status-mouse-live.sh
bash examples/nlp2hillm/apply-temperature-live.sh

# Optional LLM (skips without OPENROUTER_API_KEY)
bash examples/nlp2hillm/llm-openrouter.sh
```

## Python API

```python
from nlp2hillm.to_dsl import to_dsl, to_dsl_with_backend

# Map only
line = to_dsl("read temperature from serial", use_llm=False)

# Map with backend label
line, backend = to_dsl_with_backend("read temperature from serial")
# backend == "rules" or "llm"

# Force LLM
line, backend = to_dsl_with_backend("read temperature from serial", force_llm=True)
```

Execute from Python:

```python
from dsl2hillm import dispatch
from hillm.project_env import apply_execution_policy, bootstrap_project_env
from nlp2hillm.to_dsl import to_dsl

bootstrap_project_env()
line = apply_execution_policy(to_dsl("read temperature from serial"), live=False)
result = dispatch(line)
print(result.to_dict())
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Only DSL line, no temperature value | Map-only mode (no `--apply`) | Add `--apply` or `--apply --live` |
| `"value": "dry:temperature"` | Dry-run simulation | Add `--live`; check `HILLM_DRY_RUN` |
| `pyserial not installed` | Missing serial extra | `uv sync --extra serial` |
| Wrong serial port | Default `/dev/ttyUSB0` missing | Auto-fallback to `/dev/ttyACM0` when present; or `HILLM_SENSOR_TEMP_ADDRESS=...` |
| Mouse "port" is a list of paths | USB mouse uses `/dev/input/by-id`, not tty | Expected; filter entries containing `mouse` |
| `--use-llm` same as rules | Clear pattern uses rules by default | Use `-v`; add `--use-llm` only to force LLM |
| LLM picks wrong device | Model ignored hints | Rules are preferred for known patterns; LLM gets `suggested_dsl` in payload |

## See also

- [examples/nlp2hillm/](../../examples/nlp2hillm/) — runnable smoke scripts
- [docs/configuration.md](../../docs/configuration.md) — env vars, dry-run policy
- [docs/control-layer.md](../../docs/control-layer.md) — full adapter stack
- [Control layer packages](../README.md)

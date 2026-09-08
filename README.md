# hillm — Hardware Interface LLM


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.6-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.77-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-12.1h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.7734 (14 commits)
- 👤 **Human dev:** ~$1208 (12.1h @ $100/h, 30min dedup)

Generated on 2026-07-07 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Control platform hardware through a unified registry and transport layer:

- **Displays / HDMI** — `xrandr`, `wlr-randr`
- **Cameras** — V4L (`/dev/video*`)
- **Audio** — microphones / speakers via PulseAudio
- **Input** — keyboard / mouse discovery (`/dev/input`)
- **USB** — `lsusb` enumeration
- **Serial / RS232 / RS485** — `pyserial`
- **Modbus RTU/TCP** — `pymodbus`
- **MQTT / HTTP** — network device gateways

Pairs with:

| Package | Role |
|---------|------|
| [`gillm`](../gillm/) | GUI / IDE keyboard injection |
| [`tillm`](../tillm/) | Shell LLM clients (aider, codex, …) |
| **`hillm`** | Physical devices and field interfaces |

## Install

```bash
cd /home/tom/github/semcod/hillm
make install-dev          # uv sync + control layer (recommended)
cp examples/env.example .env   # HILLM_DRY_RUN=1 for safe local dev
make install-transports   # + serial/modbus/mqtt
make help                 # all targets
```

Or manually:

```bash
uv sync --all-packages --extra dev   # recommended (workspace + dev tools)
# pip fallback:
pip install -e ".[dev]"
bash packages/install-dev.sh         # editable *2hillm adapters
pip install -e ".[serial,modbus,mqtt]"   # optional transports
```

## CLI

```bash
hillm devices
hillm scan
hillm read --device camera-usb --dry-run
hillm write --device actuator-relay --value 1 --register coil:0 --dry-run
hillm actuate --device display-primary --action on
hillm status --ecosystem
```

## DSL / integrations

```bash
# DSL — hardware verbs dry-run by default
dsl2hillm HEALTH
dsl2hillm 'READ DEVICE sensor-temp'

# URI — dry-run by default; --live for real hardware
uri2hillm HEALTH
uri2hillm 'READ DEVICE sensor-temp'
uri2hillm 'hillm://cmd/READ?device=camera-usb&dry_run=true'

# NLP — --apply is dry-run by default
nlp2hillm "read temperature from serial"
nlp2hillm "read temperature from serial" --apply
nlp2hillm "read temperature from serial" --apply --live

# REST (port 8218)
rest2hillm --port 8218
curl -X POST http://127.0.0.1:8218/v1/dsl -d HEALTH

# nlp2uri: pip install nlp2uri[hillm]
uri2hillm 'hillm://cmd/HEALTH'
```

Dry-run policy per adapter: [docs/control-layer.md](docs/control-layer.md#dry-run-policy).

## Architecture

```
hillm (core)
  registry.py      — device catalog + aliases + suggest_device_ids()
  resolve.py       — NL keywords → device id (shared by nlp2hillm)
  project_env.py   — .env bootstrap + apply_execution_policy()
  controller.py    — read / write / actuate / connect
  transports/      — serial, modbus, mqtt, display, v4l, audio, usb, …
  compat.py        — Koru backend + tool registry exports

packages/
  dsl2hillm        — CQRS bus (single mutation point)
  uri2hillm        — hillm:// URI + DSL shorthand
  nlp2hillm        — NL → DSL (--apply dry-run default)
  cli2hillm        — shell passthrough
  mcp2hillm        — MCP tools
  rest2hillm       — REST API (:8218)
```

## Examples

Runnable smoke scripts in [examples/](examples/) — full index: [examples/README.md](examples/README.md).

```bash
bash packages/install-dev.sh
cp examples/env.example .env    # optional
bash examples/run-all-dry-run.sh
make test-examples
```

| Category | Scripts |
|----------|---------|
| **CLI** | [devices](examples/cli/devices.sh) · [scan](examples/cli/scan.sh) · [read dry-run](examples/cli/read-dry-run.sh) · [status ecosystem](examples/cli/status-ecosystem.sh) · [status mouse](examples/cli/status-mouse-dry-run.sh) |
| **DSL** | [smoke](examples/dsl/run-smoke.sh) · [read sensor-temp](examples/dsl/read-sensor-temp.sh) · [devices usb](examples/dsl/devices-usb.sh) |
| **NLP** | [temperature](examples/nlp2hillm/to-dsl-temperature.sh) · [mouse port PL](examples/nlp2hillm/to-dsl-mouse-port-pl.sh) · [apply live temp](examples/nlp2hillm/apply-temperature-live.sh) · [check serial](examples/nlp2hillm/check-serial-env.sh) |
| **URI** | [dispatch](examples/control-layer/uri-dispatch.sh) · [shorthand read](examples/control-layer/uri-shorthand-read.sh) · [decode](examples/control-layer/uri-decode-sensor.sh) |
| **Devices** | [display](examples/devices/display/status.sh) · [camera](examples/devices/camera/capture-dry-run.sh) · [mouse live](examples/devices/input/mouse-status-live.sh) · [sensor temp](examples/devices/sensor/temp-read-dry-run.sh) · [serial resolve](examples/devices/sensor/temp-resolve-address.sh) |

## Tests

```bash
make test              # core + control layer (70+ tests)
make test-examples     # examples/**/*.sh smoke (40+ scripts)
make examples          # bash examples/run-all-dry-run.sh
```

## Local complexity gate

Run `make quality-regix` before publishing source changes. It requires `regix`
with the Lizard backend (verified with Regix 0.1.15); select an isolated executable
with `make quality-regix REGIX=/path/to/regix` when needed.

The gate reads the current working tree, including uncommitted source, under
`src/` and every `packages/*/src/` adapter. It exits nonzero above CC 15 or
100 lines per function. Tests, examples and build output are outside its scope.
Coverage, documentation and maintainability have no enforced baseline in this
configuration. This opt-in local command does not install hooks or replace the
independent OneDev test and Validator publication process.

## Local regression watcher

After installing the development workspace, run `make watch-tests` in the
checkout being edited. Wup and TestQL must be available (verified with Wup
0.2.64 and TestQL 1.2.67); override `WUP` and `TESTQL` with executable paths
when needed. The watcher runs in the foreground; stop it with Ctrl-C.

Changes in core or adapter Python files trigger the pinned quick scenario
(103 focused regression cases). A quick failure triggers the full test suite;
traces and the generated runtime configuration stay in ignored `.wup/`. Generated files are excluded, periodic HTTP
probes and external reporting are disabled. The test runner forces dry-run by
default and imports source from this checkout, even with a shared test Python.
Wup 0.2.64 ignores test directories even if listed as watch roots; for test-only
edits, run `bash scripts/wup-tests.sh quick` or `detail` manually.
An incomplete environment fails with setup guidance instead of auto-installing.
This development watcher does not replace protected OneDev verification.

## Documentation

| Doc | Content |
|-----|---------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/configuration.md](docs/configuration.md) | Env vars, install profiles, ports |
| [docs/control-layer.md](docs/control-layer.md) | `*2hillm` adapters (DSL, URI, REST, MCP) |
| [packages/README.md](packages/README.md) | Control layer package matrix |
| [examples/README.md](examples/README.md) | Runnable smoke scripts |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [TODO.md](TODO.md) | Roadmap and open items |

## Environment

| Variable | Purpose |
|----------|---------|
| `HILLM_DRY_RUN` | Force dry-run transport globally |
| `OPENROUTER_API_KEY` | Enable LLM mapping in `nlp2hillm` (via litellm) |
| `LLM_MODEL` | OpenRouter model (default: `openrouter/qwen/qwen3-coder-next`) |
| `HILLM_MODBUS_HOST` | Default Modbus TCP host |
| `HILLM_MQTT_URL` | Default MQTT broker URL |
| `HILLM_<DEVICE>_ADDRESS` | Per-device address override |

## License

Licensed under Apache-2.0.

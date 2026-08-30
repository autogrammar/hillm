#!/usr/bin/env bash
# Verify nlp2hillm/hillm install and serial port resolution for sensor-temp.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$root/examples/load-env.sh"

# Prefer .venv (canonical project env); legacy venv/ may be stale.
if [[ -x "$root/.venv/bin/nlp2hillm" ]]; then
  NLP2HILLM="$root/.venv/bin/nlp2hillm"
elif [[ -x "$root/venv/bin/nlp2hillm" ]]; then
  NLP2HILLM="$root/venv/bin/nlp2hillm"
else
  NLP2HILLM="$(command -v nlp2hillm)"
fi
# Use the interpreter from the same env as the CLI so imports match.
PY="$(dirname "$NLP2HILLM")/python3"
[[ -x "$PY" ]] || PY=python3

echo "=== nlp2hillm ==="
echo "$NLP2HILLM"
ls -la "$NLP2HILLM"

"$NLP2HILLM" --help >/dev/null
"$PY" -c "
import hillm
from importlib.util import find_spec
from hillm.registry import get_device_spec, first_existing_serial_path
spec = get_device_spec('sensor-temp')
nlp_spec = find_spec('nlp2hillm')
print('hillm:', hillm.__file__)
print('nlp2hillm:', getattr(nlp_spec, 'origin', nlp_spec))
print('sensor-temp address:', spec.resolve_address())
print('first serial port:', first_existing_serial_path('/dev/ttyUSB0', '/dev/ttyACM0') or '(none)')
"

if ! "$PY" -c "
from hillm.registry import first_existing_serial_path
import sys
sys.exit(0 if first_existing_serial_path('/dev/ttyUSB0', '/dev/ttyACM0') else 2)
"; then
  echo "check-serial-env ok"
  exit 0
fi

unset HILLM_DRY_RUN
out="$("$NLP2HILLM" 'read temperature from serial' --no-llm -v --apply --live 2>&1)"
echo "$out" | grep -q '# device: sensor-temp'
echo "$out" | grep -q "address '/dev/ttyACM0'\|address '/dev/ttyUSB0'"
echo "$out" | grep -q '"backend": "serial"\|"backend": "dry_run"'
echo "check-serial-env ok"

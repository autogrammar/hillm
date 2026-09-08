#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$task_root"
test_python="${HILLM_TEST_PYTHON:-$task_root/.venv/bin/python}"
if [[ ! -x "$test_python" ]]; then
    printf 'Missing test Python: %s. Install the Hillm dev workspace first.\n' "$test_python" >&2
    exit 2
fi
export HILLM_DRY_RUN=1
export PYTHONPATH="$task_root/src"
for adapter_src in "$task_root"/packages/*/src; do
    [[ -d "$adapter_src" ]] && PYTHONPATH="$PYTHONPATH:$adapter_src"
done
case "${1:-quick}" in
    quick)
        exec "$test_python" -m pytest --noconftest -q -p no:cacheprovider \
            tests/test_controller_dispatch.py tests/test_nlp_rule_priority.py \
            tests/test_nlp_cli_diagnostics.py tests/test_uri_cli_execution.py
        ;;
    detail)
        # Avoid conftest's automatic install on an incomplete development checkout.
        for cli in hillm dsl2hillm uri2hillm nlp2hillm cli2hillm; do
            if [[ ! -x "$task_root/.venv/bin/$cli" ]]; then
                printf 'Missing .venv/bin/%s. Install the Hillm dev workspace first.\n' "$cli" >&2
                exit 2
            fi
        done
        exec "$test_python" -m pytest -q -rs -p no:cacheprovider tests
        ;;
    *) printf 'Usage: %s [quick|detail]\n' "$0" >&2; exit 2 ;;
esac

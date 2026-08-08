from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from nlp2hillm.contracts import CONTRACT_VERSION, load_schema, validate_payload
from nlp2hillm.llm_backend import nl_to_dsl_line

CONTRACTS = Path(__file__).parents[1] / "src" / "nlp2hillm" / "contracts" / "v1"
FIXTURES = Path(__file__).parent / "fixtures" / "contracts" / "v1"


class _FakeBackend:
    response_format = None

    def complete(self, *, model, messages, temperature=0.2, response_format=None) -> str:
        self.response_format = response_format
        return '{"contractVersion":"1.0.0","dsl":"READ DEVICE sensor-temp REGISTER temperature"}'


def test_nl_to_dsl_line_fake_backend() -> None:
    backend = _FakeBackend()
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-test"}, clear=False):
        line = nl_to_dsl_line("read temperature from serial", backend=backend)
    assert line == "READ DEVICE sensor-temp REGISTER temperature"
    assert backend.response_format["json_schema"]["schema"] == load_schema()


def test_nl_to_dsl_line_without_api_key() -> None:
    with patch.dict("os.environ", {}, clear=True):
        assert nl_to_dsl_line("read temperature") is None


def test_valid_and_invalid_fixtures() -> None:
    valid = json.loads((FIXTURES / "valid-dsl-line.json").read_text())
    validate_payload(valid)
    invalid = json.loads((FIXTURES / "invalid-dsl-line.json").read_text())
    with pytest.raises(ValueError, match="violates DslLineResponse v1"):
        validate_payload(invalid)


@pytest.mark.parametrize(
    "content",
    [
        '```json\n{"contractVersion":"1.0.0","dsl":"HEALTH"}\n```',
        '{"contractVersion":"2.0.0","dsl":"HEALTH"}',
        '{"contractVersion":"1.0.0","dsl":"SHELL rm"}',
        '{"contractVersion":"1.0.0","dsl":"HEALTH","extra":true}',
    ],
)
def test_malformed_or_unsafe_output_fails_closed(content: str) -> None:
    class Backend(_FakeBackend):
        def complete(self, **kwargs) -> str:
            return content

    assert nl_to_dsl_line("status", backend=Backend()) is None


def test_manifest_binds_all_artifacts() -> None:
    manifest = json.loads((CONTRACTS / "manifest.json").read_text())
    assert manifest["version"] == CONTRACT_VERSION
    assert manifest["boundary"] == "nlp2hillm.llm_backend.nl_to_dsl_line"
    for artifact in manifest["artifacts"].values():
        assert (CONTRACTS / artifact).is_file()
    assert "message DslLineResponse" in (CONTRACTS / "dsl-line.proto").read_text()
    assert f'\\"{CONTRACT_VERSION}\\"' in (CONTRACTS / "dsl-line.gbnf").read_text()

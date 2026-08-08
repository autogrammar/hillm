from unittest.mock import patch

import pytest
from nlp2hillm.to_dsl import resolve_device, to_dsl


def test_to_dsl_temperature_from_serial() -> None:
    assert to_dsl("read temperature from serial") == "READ DEVICE sensor-temp REGISTER temperature"


def test_to_dsl_polish_mouse_port() -> None:
    assert to_dsl("na jakim porcie jest podłączona myszka?") == "STATUS DEVICE mouse-default"


def test_to_dsl_camera_capture() -> None:
    line = to_dsl("capture image from camera")
    assert line == "ACTUATE DEVICE camera-usb ACTION capture"


def test_to_dsl_connect_modbus() -> None:
    assert to_dsl("connect modbus device") == "CONNECT DEVICE modbus-rtu"


def test_to_dsl_list_usb_polish() -> None:
    assert to_dsl("jakie urządzenia usb są podłączone") == "DEVICES CATEGORY usb"


def test_to_dsl_health_passthrough() -> None:
    assert to_dsl("HEALTH") == "HEALTH"


def test_resolve_device_prefers_mouse_over_usb() -> None:
    assert resolve_device("read usb port for mouse") == "mouse-default"


def test_resolve_device_temperature_serial_combo() -> None:
    assert resolve_device("read temperature from serial") == "sensor-temp"


def test_to_dsl_usb_port_for_mouse() -> None:
    assert to_dsl("read usb port for mouse") == "READ DEVICE mouse-default"


def test_to_dsl_status_mouse_port() -> None:
    assert to_dsl("what port is the mouse on") == "STATUS DEVICE mouse-default"


def test_to_dsl_prefers_rules_when_key_set_and_clear_hint() -> None:
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-test"}, clear=False):
        line = to_dsl("read temperature from serial")
    assert line == "READ DEVICE sensor-temp REGISTER temperature"


def test_to_dsl_uses_llm_for_ambiguous_when_key_set() -> None:
    class _FakeBackend:
        def complete(self, *, model, messages, temperature=0.2, response_format=None) -> str:
            return '{"contractVersion":"1.0.0","dsl":"READ DEVICE modbus-rtu REGISTER holding:0"}'

    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-test"}, clear=False):
        line = to_dsl(
            "what is the value on the fieldbus gateway",
            llm_backend=_FakeBackend(),
        )
    assert line == "READ DEVICE modbus-rtu REGISTER holding:0"


def test_to_dsl_force_llm_raises_when_llm_fails() -> None:
    class _FailBackend:
        def complete(self, *, model, messages, temperature=0.2, response_format=None) -> str:
            raise RuntimeError("api down")

    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-test"}, clear=False):
        with pytest.raises(ValueError, match="LLM mapping failed"):
            to_dsl(
                "read temperature from serial",
                force_llm=True,
                llm_backend=_FailBackend(),
            )


def test_to_dsl_force_llm_overrides_rules() -> None:
    class _FakeBackend:
        def complete(self, *, model, messages, temperature=0.2, response_format=None) -> str:
            return (
                '{"contractVersion":"1.0.0","dsl":'
                '"READ DEVICE serial-ttyusb0 REGISTER temperature"}'
            )

    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-test"}, clear=False):
        line = to_dsl(
            "read temperature from serial",
            force_llm=True,
            llm_backend=_FakeBackend(),
        )
    assert line == "READ DEVICE serial-ttyusb0 REGISTER temperature"


def test_to_dsl_no_llm_uses_rules() -> None:
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-test"}, clear=False):
        assert to_dsl("read temperature from serial", use_llm=False) == (
            "READ DEVICE sensor-temp REGISTER temperature"
        )

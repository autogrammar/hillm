"""Characterize request dispatch without invoking hardware transports."""

import pytest

from hillm import controller
from hillm.contracts.device import DeviceResult
from hillm.controller import HardwareRequest, execute_request


@pytest.mark.parametrize("action", ["connect", "disconnect", "read", "write", "actuate", "status"])
@pytest.mark.parametrize("address,register,value", [("", "", 0), ("port", "reg", "move")])
def test_dispatch_contract(monkeypatch, action, address, register, value):
    calls = []
    result = DeviceResult(ok=True, device_id="sentinel")

    def backend(*args, **kwargs):
        calls.append((args, kwargs))
        return result

    monkeypatch.setattr(controller, f"{action}_device", backend)
    options = {"timeout": 3}
    request = HardwareRequest(
        "temperature", f" {action.upper()} ", address, register, value, True, options
    )
    assert execute_request(request) is result
    expected_args = ("sensor-temp",)
    expected_kwargs = {"address": address or None, "dry_run": True, "timeout": 3}
    if action in {"read", "write"}:
        expected_kwargs["register"] = register or None
    if action == "write":
        expected_args += (value,)
    if action == "actuate":
        expected_args += (str(value or register or "run"),)
        expected_kwargs["register"] = register
    assert calls == [(expected_args, expected_kwargs)]
    assert options == {"timeout": 3}


@pytest.mark.parametrize("action", ["connect", "disconnect", "read", "write", "actuate", "status"])
def test_duplicate_options_still_raise(action):
    with pytest.raises(TypeError, match="address"):
        execute_request(HardwareRequest("sensor-temp", action, options={"address": "duplicate"}))


def test_unsupported_action_keeps_original_text():
    with pytest.raises(ValueError, match="unsupported hardware action:  UNKNOWN "):
        execute_request(HardwareRequest("sensor-temp", " UNKNOWN "))

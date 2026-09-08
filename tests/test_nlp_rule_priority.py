"""Preserve NLP rule priority and temperature register fallbacks."""

from importlib import import_module
from types import SimpleNamespace

import pytest

mapper = import_module("nlp2hillm.to_dsl")


@pytest.mark.parametrize(
    "prompt, expected",
    [
        (" health ", "HEALTH"),
        ("devices", "DEVICES"),
        ("orient", "ORIENT"),
        ("actions", "ACTIONS"),
        ("lista urządzen usb read temperature", "DEVICES CATEGORY usb"),
        ("connect write temperature off", "CONNECT DEVICE sensor"),
        ("połącz temperature", "CONNECT DEVICE sensor"),
        ("write capture temperature off", "WRITE DEVICE sensor VALUE off"),
        ("ustaw temperature", "WRITE DEVICE sensor VALUE on"),
        ("write coffee", "WRITE DEVICE sensor VALUE off"),
        ("capture camera temperature", "ACTUATE DEVICE sensor ACTION capture"),
        ("enable relay temperature", "ACTUATE DEVICE sensor ACTION on"),
        ("status temperature", "READ DEVICE sensor REGISTER custom"),
        ("odczytaj temperatur", "READ DEVICE sensor REGISTER custom"),
        ("read status", "READ DEVICE sensor"),
        ("status", "STATUS DEVICE sensor"),
        ("unknown request", "STATUS DEVICE sensor"),
        ("temperatureish", "STATUS DEVICE sensor"),
    ],
)
def test_rule_priority(monkeypatch, prompt, expected):
    monkeypatch.setattr(mapper, "resolve_device_from_text", lambda text: "sensor")
    monkeypatch.setattr(
        mapper, "get_device_spec", lambda device: SimpleNamespace(default_register="custom")
    )
    assert mapper.to_dsl_with_backend(prompt, use_llm=False) == (expected, "rules")


@pytest.mark.parametrize("spec", [None, SimpleNamespace(default_register="")])
def test_temperature_register_fallback(monkeypatch, spec):
    monkeypatch.setattr(mapper, "resolve_device_from_text", lambda text: "sensor")
    monkeypatch.setattr(mapper, "get_device_spec", lambda device: spec)
    assert mapper.to_dsl("read temp", use_llm=False) == ("READ DEVICE sensor REGISTER temperature")


@pytest.mark.parametrize("prompt", ["read sensor", "write temp", "connect temp", "capture temp"])
def test_unneeded_register_lookup_is_not_performed(monkeypatch, prompt):
    def unexpected_lookup(device):
        pytest.fail("command must not resolve a temperature register")

    monkeypatch.setattr(mapper, "get_device_spec", unexpected_lookup)
    assert mapper.to_dsl(prompt, use_llm=False)


@pytest.mark.parametrize("prompt", ["", " \n "])
def test_empty_prompt_error(prompt):
    with pytest.raises(ValueError, match="^empty prompt$"):
        mapper.to_dsl(prompt, use_llm=False)

from __future__ import annotations

import os
import re

from nlp2hillm.llm_backend import LLMBackend, nl_to_dsl_line

from hillm.registry import get_device_spec
from hillm.resolve import default_serial_device, resolve_device_from_text

_READ_RE = re.compile(r"\b(read|odczytaj|pobierz)\b", re.I)
_WRITE_RE = re.compile(r"\b(write|zapisz|ustaw)\b", re.I)
_CONNECT_RE = re.compile(r"\b(connect|polacz|połącz)\b", re.I)
_ACTUATE_RE = re.compile(r"\b(actuate|capture|snapshot|mute|unmute|enable|disable)\b", re.I)
_STATUS_RE = re.compile(
    r"\b(status|stan|port|portu|podłącz|podlacz|connected|connection|"
    r"podłączon|podlaczon|na\s+jakim\s+porcie)\b",
    re.I,
)


def resolve_device(prompt: str) -> str:
    return resolve_device_from_text(prompt)


def _has_clear_rule_match(prompt: str) -> bool:
    """True when rule-based mapper has a confident device/verb mapping."""
    text = prompt.strip()
    if not text:
        return False
    upper = text.upper()
    if upper in {"HEALTH", "DEVICES", "ORIENT", "ACTIONS"}:
        return True
    lowered = text.lower()
    if re.search(r"\b(list|lista|jakie)\b.*\b(usb|urządzen|urzadzen|devices)\b", lowered):
        return True
    device = resolve_device_from_text(text)
    if device != default_serial_device():
        return True
    if (
        _READ_RE.search(text)
        or _WRITE_RE.search(text)
        or _CONNECT_RE.search(text)
        or _ACTUATE_RE.search(text)
        or _STATUS_RE.search(text)
    ):
        return bool(
            re.search(
                r"\b(temp|temperature|mouse|mysz|usb|camera|modbus|mqtt|hdmi|display|relay)\b",
                text,
                re.I,
            )
        )
    return False


def _temperature_register(text: str, device: str) -> str:
    if not re.search(r"\b(temp|temperature|temperatur)\b", text, re.I):
        return ""
    spec = get_device_spec(device)
    return (spec.default_register if spec else "") or "temperature"


def _rule_to_dsl(prompt: str) -> str:
    text = prompt.strip()
    if not text:
        raise ValueError("empty prompt")
    upper = text.upper()
    if upper in {"HEALTH", "DEVICES", "ORIENT", "ACTIONS"}:
        return upper
    lowered = text.lower()
    if re.search(r"\b(list|lista|jakie)\b.*\b(usb|urządzen|urzadzen|devices)\b", lowered):
        return "DEVICES CATEGORY usb"
    device = resolve_device_from_text(text)
    if _CONNECT_RE.search(text):
        return f"CONNECT DEVICE {device}"
    if _WRITE_RE.search(text):
        value = "on"
        if "off" in lowered:
            value = "off"
        return f"WRITE DEVICE {device} VALUE {value}"
    if _ACTUATE_RE.search(text):
        action = "capture" if re.search(r"\b(camera|webcam|kamera)\b", text, re.I) else "on"
        return f"ACTUATE DEVICE {device} ACTION {action}"
    register = _temperature_register(text, device)
    if register:
        return f"READ DEVICE {device} REGISTER {register}"
    if _READ_RE.search(text):
        return f"READ DEVICE {device}"
    if _STATUS_RE.search(text):
        return f"STATUS DEVICE {device}"
    return f"STATUS DEVICE {device}"


def to_dsl_with_backend(
    prompt: str,
    *,
    use_llm: bool | None = None,
    force_llm: bool = False,
    llm_backend: LLMBackend | None = None,
) -> tuple[str, str]:
    """Return (dsl_line, backend) where backend is ``rules`` or ``llm``."""
    rule_line = _rule_to_dsl(prompt)

    if use_llm is None:
        use_llm = bool(os.getenv("OPENROUTER_API_KEY", "").strip())

    if force_llm and use_llm:
        llm_line = nl_to_dsl_line(prompt, backend=llm_backend)
        if llm_line:
            return llm_line, "llm"
        raise ValueError(
            "LLM mapping failed (--use-llm). Check OPENROUTER_API_KEY, "
            "pip install nlp2hillm[llm], and network access."
        )

    if use_llm and not _has_clear_rule_match(prompt):
        llm_line = nl_to_dsl_line(prompt, backend=llm_backend)
        if llm_line:
            return llm_line, "llm"

    return rule_line, "rules"


def to_dsl(
    prompt: str,
    *,
    use_llm: bool | None = None,
    force_llm: bool = False,
    llm_backend: LLMBackend | None = None,
) -> str:
    line, _backend = to_dsl_with_backend(
        prompt,
        use_llm=use_llm,
        force_llm=force_llm,
        llm_backend=llm_backend,
    )
    return line

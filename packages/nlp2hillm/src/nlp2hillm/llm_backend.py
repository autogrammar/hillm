"""LLM backend for nlp2hillm NL → DSL (OpenRouter via litellm + .env)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from nlp2hillm.contracts import response_format, validate_payload


@runtime_checkable
class LLMBackend(Protocol):
    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        ...


class LitellmBackend:
    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        import litellm  # type: ignore

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        if model.startswith("openrouter/"):
            app_name = (
                os.getenv("OPENROUTER_APP_NAME", "").strip()
                or Path.cwd().name
                or "hillm"
            )
            headers = {"X-Title": app_name}
            app_url = os.getenv("OPENROUTER_APP_URL", "").strip()
            if app_url:
                headers["HTTP-Referer"] = app_url
            kwargs["extra_headers"] = headers
        response = litellm.completion(**kwargs)
        return (response.choices[0].message.content or "").strip()


def get_backend(backend: LLMBackend | None = None) -> LLMBackend:
    if backend is not None:
        return backend
    return LitellmBackend()


def _device_catalog() -> str:
    from hillm.registry import iter_device_specs

    lines: list[str] = []
    for spec in iter_device_specs():
        aliases = ", ".join(spec.aliases) if spec.aliases else spec.label
        lines.append(f"- {spec.id} ({spec.category}): {aliases}")
    return "\n".join(lines)


def _validate_dsl_line(line: str) -> str | None:
    try:
        from dsl2hillm.grammar import parse_line

        payload = parse_line(line)
        if not payload:
            return None
        return line.strip()
    except Exception:
        return None


def _rule_hint(prompt: str) -> dict[str, str]:
    try:
        from nlp2hillm.to_dsl import _has_clear_rule_match, _rule_to_dsl

        if not _has_clear_rule_match(prompt):
            return {}
        return {"suggested_dsl": _rule_to_dsl(prompt)}
    except Exception:
        return {}


def nl_to_dsl_line(
    prompt: str,
    *,
    model: str | None = None,
    backend: LLMBackend | None = None,
) -> str | None:
    """Convert NL prompt to a single dsl2hillm command line via LLM."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key and backend is None:
        return None
    resolved_model = model or os.getenv("LLM_MODEL", "openrouter/z-ai/glm-5.2")
    llm = get_backend(backend)
    system = (
        "Convert the user request to ONE dsl2hillm command line for hardware control.\n"
        "Query verbs: HEALTH, DEVICES, ORIENT, ACTIONS, VALIDATE, READ, STATUS, RESOLVE\n"
        "Command verbs: WRITE, ACTUATE, CONNECT, DISCONNECT, EXECUTE\n"
        "Use DEVICE <id> from the catalog. Optional flags: REGISTER, VALUE, ACTION, CATEGORY.\n"
        "Do not add DRY_RUN unless the user explicitly asks for simulation/dry-run.\n"
        "Mapping hints:\n"
        "- temperature/temp from serial → DEVICE sensor-temp REGISTER temperature\n"
        "- mouse over usb → DEVICE mouse-default\n"
        "- generic usb list → DEVICE usb-hub\n"
        "- modbus → DEVICE modbus-rtu or modbus-tcp\n"
        "Return one DslLineResponse 1.0.0 JSON object only: "
        '{"contractVersion":"1.0.0","dsl":"READ DEVICE sensor-temp REGISTER temperature"}\n'
        "Device catalog:\n"
        f"{_device_catalog()}"
    )
    try:
        user_payload = {"prompt": prompt, **_rule_hint(prompt)}
        content = llm.complete(
            model=resolved_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            response_format=response_format(),
        )
        data = json.loads(content)
        validate_payload(data)
        dsl = data["dsl"].strip()
        return _validate_dsl_line(dsl)
    except Exception:  # noqa: BLE001 - provider failures deliberately trigger rules fallback
        return None

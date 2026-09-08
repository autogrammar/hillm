"""Hardware read/write/actuate orchestration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from hillm.contracts.device import DeviceResult
from hillm.registry import DeviceSpec, format_unknown_device, get_device_spec, normalize_device_id
from hillm.transports.base import get_transport


@dataclass(frozen=True)
class HardwareRequest:
    device_id: str
    action: str
    address: str = ""
    register: str = ""
    value: Any = None
    dry_run: bool = False
    options: dict[str, Any] | None = None


def _resolve_spec(device_id: str) -> DeviceSpec:
    spec = get_device_spec(device_id)
    if spec is None:
        raise ValueError(format_unknown_device(device_id))
    return spec


def _backend_for(spec: DeviceSpec, *, dry_run: bool) -> Any:
    transport_id = "dry_run" if dry_run else spec.transport
    if os.environ.get("HILLM_DRY_RUN", "").strip().lower() in {"1", "true", "yes", "on"}:
        transport_id = "dry_run"
    return get_transport(transport_id)


def _with_device_id(result: DeviceResult, spec: DeviceSpec) -> DeviceResult:
    return DeviceResult(
        ok=result.ok,
        device_id=spec.id,
        backend=result.backend,
        value=result.value,
        message=result.message,
        data=result.data,
        error=result.error,
    )


def connect_device(
    device_id: str, *, address: str | None = None, dry_run: bool = False, **options: Any
) -> DeviceResult:
    spec = _resolve_spec(device_id)
    backend = _backend_for(spec, dry_run=dry_run)
    result = backend.connect(address=spec.resolve_address(address), **options)
    return _with_device_id(result, spec)


def disconnect_device(
    device_id: str, *, address: str | None = None, dry_run: bool = False, **options: Any
) -> DeviceResult:
    spec = _resolve_spec(device_id)
    backend = _backend_for(spec, dry_run=dry_run)
    result = backend.disconnect(address=spec.resolve_address(address), **options)
    return _with_device_id(result, spec)


def read_device(
    device_id: str,
    *,
    register: str | None = None,
    address: str | None = None,
    dry_run: bool = False,
    **options: Any,
) -> DeviceResult:
    spec = _resolve_spec(device_id)
    backend = _backend_for(spec, dry_run=dry_run)
    result = backend.read(
        address=spec.resolve_address(address),
        register=register or spec.default_register,
        **options,
    )
    return _with_device_id(result, spec)


def write_device(
    device_id: str,
    value: Any,
    *,
    register: str | None = None,
    address: str | None = None,
    dry_run: bool = False,
    **options: Any,
) -> DeviceResult:
    spec = _resolve_spec(device_id)
    backend = _backend_for(spec, dry_run=dry_run)
    result = backend.write(
        address=spec.resolve_address(address),
        value=value,
        register=register or spec.default_register,
        **options,
    )
    return _with_device_id(result, spec)


def actuate_device(
    device_id: str,
    action: str,
    *,
    address: str | None = None,
    dry_run: bool = False,
    **params: Any,
) -> DeviceResult:
    spec = _resolve_spec(device_id)
    backend = _backend_for(spec, dry_run=dry_run)
    result = backend.actuate(address=spec.resolve_address(address), action=action, **params)
    return _with_device_id(result, spec)


def status_device(
    device_id: str, *, address: str | None = None, dry_run: bool = False, **options: Any
) -> DeviceResult:
    spec = _resolve_spec(device_id)
    backend = _backend_for(spec, dry_run=dry_run)
    result = backend.status(address=spec.resolve_address(address), **options)
    return _with_device_id(result, spec)


def _execute_register_request(
    request: HardwareRequest,
    device_id: str,
    action: str,
    options: dict[str, Any],
) -> DeviceResult:
    """Dispatch an already normalized read or write request."""
    if action == "read":
        return read_device(
            device_id,
            register=request.register or None,
            address=request.address or None,
            dry_run=request.dry_run,
            **options,
        )
    return write_device(
        device_id,
        request.value,
        register=request.register or None,
        address=request.address or None,
        dry_run=request.dry_run,
        **options,
    )


def execute_request(request: HardwareRequest) -> DeviceResult:
    device_id = normalize_device_id(request.device_id)
    action = request.action.strip().lower()
    options = dict(request.options or {})
    if action == "connect":
        return connect_device(
            device_id, address=request.address or None, dry_run=request.dry_run, **options
        )
    if action == "disconnect":
        return disconnect_device(
            device_id, address=request.address or None, dry_run=request.dry_run, **options
        )
    if action in {"read", "write"}:
        return _execute_register_request(request, device_id, action, options)
    if action == "actuate":
        return actuate_device(
            device_id,
            str(request.value or request.register or "run"),
            address=request.address or None,
            dry_run=request.dry_run,
            register=request.register,
            **options,
        )
    if action == "status":
        return status_device(
            device_id, address=request.address or None, dry_run=request.dry_run, **options
        )
    raise ValueError(f"unsupported hardware action: {request.action}")

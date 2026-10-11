"""HILLM CLI — hardware device control."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from hillm.controller import (
    actuate_device,
    connect_device,
    disconnect_device,
    read_device,
    status_device,
    write_device,
)
from hillm.discovery.scan import scan_host
from hillm.project_env import bootstrap_project_env
from hillm.registry import detect_devices
from hillm.validation import ecosystem_status, validate_device_readiness


def _print_json(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _devices_cmd(args: argparse.Namespace) -> int:
    rows = detect_devices(category=args.category or None)
    if args.format == "json":
        _print_json(rows)
    else:
        for row in rows:
            status = "ready" if row.get("ready") else "missing"
            print(f"{row['id']:20} {row['category']:10} {row['transport']:10} [{status}] {row['label']}")
    return 0


def _scan_cmd(args: argparse.Namespace) -> int:
    data = scan_host()
    _print_json(data)
    return 0


def _status_cmd(args: argparse.Namespace) -> int:
    if args.ecosystem:
        _print_json(ecosystem_status())
        return 0
    result = status_device(args.device, dry_run=args.dry_run)
    _print_json(result.to_dict())
    return 0 if result.ok else 2


def _read_cmd(args: argparse.Namespace) -> int:
    result = read_device(args.device, register=args.register or None, dry_run=args.dry_run)
    _print_json(result.to_dict())
    return 0 if result.ok else 2


def _write_cmd(args: argparse.Namespace) -> int:
    result = write_device(
        args.device,
        args.value,
        register=args.register or None,
        dry_run=args.dry_run,
    )
    _print_json(result.to_dict())
    return 0 if result.ok else 2


def _actuate_cmd(args: argparse.Namespace) -> int:
    result = actuate_device(args.device, args.action, dry_run=args.dry_run)
    _print_json(result.to_dict())
    return 0 if result.ok else 2


def _connect_cmd(args: argparse.Namespace) -> int:
    result = connect_device(args.device, dry_run=args.dry_run)
    _print_json(result.to_dict())
    return 0 if result.ok else 2


def _disconnect_cmd(args: argparse.Namespace) -> int:
    result = disconnect_device(args.device, dry_run=args.dry_run)
    _print_json(result.to_dict())
    return 0 if result.ok else 2


def _validate_cmd(args: argparse.Namespace) -> int:
    if args.device:
        result = validate_device_readiness(args.device, action=args.action)
        _print_json(result.to_dict())
        return 0 if result.ok else 2
    _print_json(ecosystem_status())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hillm", description="Hardware Interface LLM control plane")
    sub = parser.add_subparsers(dest="command", required=True)

    devices = sub.add_parser("devices", help="List registered hardware profiles")
    devices.add_argument("--category", help="Filter by category (camera, serial, display, ...)")
    devices.add_argument("--format", choices=("table", "json"), default="table")
    devices.set_defaults(func=_devices_cmd)

    scan = sub.add_parser("scan", help="Scan host for hardware hints")
    scan.set_defaults(func=_scan_cmd)

    status = sub.add_parser("status", help="Device or ecosystem status")
    status.add_argument("--ecosystem", action="store_true", help="Show ecosystem status")
    status.add_argument("--device")
    status.add_argument("--dry-run", action="store_true")
    status.set_defaults(func=_status_cmd)

    read = sub.add_parser("read", help="Read from a device/register")
    read.add_argument("--device", required=True)
    read.add_argument("--register", default="")
    read.add_argument("--dry-run", action="store_true")
    read.set_defaults(func=_read_cmd)

    write = sub.add_parser("write", help="Write to a device/register")
    write.add_argument("--device", required=True)
    write.add_argument("--value", required=True)
    write.add_argument("--register", default="")
    write.add_argument("--dry-run", action="store_true")
    write.set_defaults(func=_write_cmd)

    actuate = sub.add_parser("actuate", help="Run a higher-level hardware action")
    actuate.add_argument("--device", required=True)
    actuate.add_argument("--action", required=True)
    actuate.add_argument("--dry-run", action="store_true")
    actuate.set_defaults(func=_actuate_cmd)

    connect = sub.add_parser("connect", help="Connect to a hardware endpoint")
    connect.add_argument("--device", required=True)
    connect.add_argument("--dry-run", action="store_true")
    connect.set_defaults(func=_connect_cmd)

    disconnect = sub.add_parser("disconnect", help="Disconnect from a hardware endpoint")
    disconnect.add_argument("--device", required=True)
    disconnect.add_argument("--dry-run", action="store_true")
    disconnect.set_defaults(func=_disconnect_cmd)

    validate = sub.add_parser("validate", help="Validate device readiness or ecosystem")
    validate.add_argument("--device")
    validate.add_argument("--action", default="read")
    validate.set_defaults(func=_validate_cmd)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        from .autoupdate import check_for_updates
        check_for_updates("hillm")
    except Exception:
        pass
    bootstrap_project_env()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())

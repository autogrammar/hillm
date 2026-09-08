from __future__ import annotations

import argparse
import json
import sys

from uri2hillm.decode import uri_to_dsl
from uri2hillm.run import run_uri
from uri2hillm.uri import normalize_uri_input

from hillm.project_env import bootstrap_project_env


def _target(argv: list[str]) -> str:
    return " ".join(argv).strip()


def _run_and_print(
    uri: str,
    *,
    default_file: str | None,
    live: bool,
    dry_run: bool,
    as_json: bool,
) -> int:
    result = run_uri(uri, default_file=default_file, live=live, dry_run=dry_run)
    if as_json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.output or result.error)
    return 0 if result.ok else 1


def _print_help() -> None:
    parser = argparse.ArgumentParser(
        prog="uri2hillm",
        description="Run hillm commands from hillm:// URIs or DSL shorthand.",
    )
    parser.print_help()
    print(
        "\nExamples:\n"
        "  uri2hillm HEALTH\n"
        "  uri2hillm READ DEVICE sensor-temp\n"
        "  uri2hillm 'hillm://cmd/READ?device=camera-usb&dry_run=true'\n"
        "  uri2hillm decode READ DEVICE sensor-temp\n"
        "  uri2hillm run READ DEVICE sensor-temp --live\n"
    )


def _execute_args(args: argparse.Namespace, *, as_json: bool) -> int:
    default_file = args.file or None
    uri = normalize_uri_input(_target(args.target), default_file=default_file)
    return _run_and_print(
        uri,
        default_file=default_file,
        live=args.live,
        dry_run=not args.live or args.dry_run,
        as_json=as_json,
    )


def main(argv: list[str] | None = None) -> int:
    bootstrap_project_env()
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv == ["-h"] or argv == ["--help"]:
        _print_help()
        return 0

    if argv[0] == "decode":
        parser = argparse.ArgumentParser(prog="uri2hillm decode")
        parser.add_argument("target", nargs="+", help="hillm:// URI or DSL line")
        parser.add_argument("--file", default="")
        args = parser.parse_args(argv[1:])
        uri = normalize_uri_input(_target(args.target), default_file=args.file or None)
        print(uri_to_dsl(uri, default_file=args.file or None))
        return 0

    if argv[0] == "run":
        parser = argparse.ArgumentParser(prog="uri2hillm run")
        parser.add_argument("target", nargs="+", help="hillm:// URI or DSL line")
        parser.add_argument("--file", default="")
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--live", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        args = parser.parse_args(argv[1:])
        return _execute_args(args, as_json=args.json)

    parser = argparse.ArgumentParser(prog="uri2hillm")
    parser.add_argument("target", nargs="+", help="hillm:// URI or DSL line")
    parser.add_argument("--file", default="")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    return _execute_args(args, as_json=True)


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import re
import sys

from dsl2hillm import dispatch
from nlp2hillm.to_dsl import to_dsl_with_backend

from hillm.project_env import apply_execution_policy, bootstrap_project_env
from hillm.registry import get_device_spec

_DEVICE_RE = re.compile(r"\bDEVICE\s+([a-z0-9-]+)", re.I)


def main(argv: list[str] | None = None) -> int:
    bootstrap_project_env()
    parser = argparse.ArgumentParser(prog="nlp2hillm")
    parser.add_argument("prompt", nargs="?", help="Natural language hardware command")
    parser.add_argument(
        "--apply", action="store_true", help="Execute mapped DSL (dry-run by default)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real hardware transports on --apply (default is dry-run)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run on --apply (default unless --live)",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Force OpenRouter LLM mapping (requires OPENROUTER_API_KEY in .env)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Use rule-based mapper only (skip LLM even when OPENROUTER_API_KEY is set)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print mapping backend (rules/llm) to stderr",
    )
    args = parser.parse_args(argv)
    if not args.prompt:
        parser.print_help()
        return 2
    use_llm = None
    if args.use_llm:
        use_llm = True
    elif args.no_llm:
        use_llm = False
    try:
        line, backend = to_dsl_with_backend(
            args.prompt,
            use_llm=use_llm,
            force_llm=args.use_llm,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.verbose:
        import os
        import sys as _sys

        if backend == "llm":
            model = os.getenv("LLM_MODEL", "openrouter/z-ai/glm-5.2")
            print(f"# mapped via: llm ({model})", file=_sys.stderr)
        else:
            print("# mapped via: rules", file=_sys.stderr)
        match = _DEVICE_RE.search(line)
        if match:
            spec = get_device_spec(match.group(1))
            if spec:
                print(f"# device: {spec.id} → address {spec.resolve_address()!r}", file=_sys.stderr)
        import importlib.util

        hillm_path = __import__("hillm").__file__ or ""
        nlp_spec = importlib.util.find_spec("nlp2hillm")
        nlp_path = getattr(nlp_spec, "origin", "") if nlp_spec else ""
        print(f"# hillm: {os.path.dirname(hillm_path)}", file=_sys.stderr)
        if nlp_path:
            print(f"# nlp2hillm: {os.path.dirname(nlp_path)}", file=_sys.stderr)
    if not args.apply:
        print(line)
        return 0
    line = apply_execution_policy(line, live=args.live, dry_run=not args.live or args.dry_run)
    result = dispatch(line)
    payload = result.to_dict()
    if args.verbose:
        payload["mapper"] = backend
    print(json.dumps(payload, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line entrypoint: `python -m gtm_cli_warmup describe "Notion"`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from .cost import cost_tracker
from .describe import DescribeError, describe_company


def _render(desc, record, *, as_json: bool) -> str:
    if as_json:
        return json.dumps(
            {"description": desc.model_dump(), "usage": record.__dict__},
            indent=2,
            default=str,
        )
    return "\n".join(
        [
            f"  name        {desc.name}",
            f"  industry    {desc.industry}",
            f"  size_guess  {desc.size_guess}",
            "",
            f"  {desc.one_liner}",
        ]
    )


def _usage_line(record) -> str:
    return (
        f"  {record.input_tokens} in / {record.output_tokens} out tokens"
        f"  ·  ${record.cost_usd:.6f}"
        f"  ·  {record.latency_ms} ms"
        f"  ·  {record.model}"
    )


def main(argv: list[str] | None = None) -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(prog="gtm_cli_warmup")
    sub = parser.add_subparsers(dest="command", required=True)

    describe = sub.add_parser("describe", help="Describe a company.")
    describe.add_argument("company", help="Company name, e.g. 'Notion'.")
    describe.add_argument("--json", action="store_true", help="Emit JSON.")
    describe.add_argument(
        "--log", type=Path, default=None, help="Path to runs.jsonl (default: ./runs.jsonl)"
    )

    args = parser.parse_args(argv)

    with cost_tracker("describe", log_path=args.log) as tracker:
        try:
            desc, record = describe_company(args.company, tracker)
        except DescribeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    print(_render(desc, record, as_json=args.json))
    if not args.json:
        print()
        print(_usage_line(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line interface for gtm-outbound-agent."""

from __future__ import annotations

import asyncio
import argparse
import sys
from pathlib import Path

from .batch import main_run, main_resume, main_list


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GTM Outbound Agent — batch process companies through the full pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")

    # `run` subcommand
    run_parser = subparsers.add_parser("run", help="Run a new batch of companies")
    run_parser.add_argument("--input", type=Path, help="Input CSV file with 'domain' column")
    run_parser.add_argument("--domains", nargs="+", help="List of domains to process")
    run_parser.add_argument("--output", type=Path, default=Path("runs"), help="Output directory")

    # `resume` subcommand
    resume_parser = subparsers.add_parser("resume", help="Resume a paused batch")
    resume_parser.add_argument("--run-id", required=True, help="Batch run ID to resume")
    resume_parser.add_argument("--output", type=Path, default=Path("runs"), help="Output directory")

    # `list` subcommand
    list_parser = subparsers.add_parser("list", help="List recent batch runs")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "run":
            asyncio.run(
                main_run(
                    input_csv=args.input,
                    domains=args.domains,
                    output_dir=args.output,
                )
            )
        elif args.command == "resume":
            asyncio.run(
                main_resume(
                    run_id=args.run_id,
                    output_dir=args.output,
                )
            )
        elif args.command == "list":
            asyncio.run(main_list())
    except KeyboardInterrupt:
        print("\n⏸ Batch paused. Resume with: python -m gtm_outbound.cli resume --run-id <run_id>")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

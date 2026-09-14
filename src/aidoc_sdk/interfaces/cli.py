"""
CLI Interface
=============

Command-line interface for AIDoc SDK.
Uses `click` for argument parsing, color output, and exit code control.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from aidoc_sdk.interfaces.api import process_file
from aidoc_sdk.core.serializer import to_canonical_json
from aidoc_sdk.pipeline.config import PipelineConfig
from aidoc_sdk.exceptions import AIDocError


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("path", type=click.Path(exists=False))
@click.option(
    "--format", "format_name",
    required=False,
    help="Explicit extractor format name (e.g. txt, pdf, docx). Auto-detected if omitted.",
)
@click.option(
    "--semantic",
    is_flag=True,
    default=False,
    help="Enable semantic enrichment via the rule engine.",
)
def main(path: str, format_name: str | None, semantic: bool) -> None:
    """Process a document into canonical AIDoc JSON."""

    config = PipelineConfig(
        enable_semantic=semantic,
        semantic_engines=["rule_engine"] if semantic else [],
    )

    try:
        document = process_file(
            path=Path(path),
            format_name=format_name,
            config=config,
        )
        click.echo(to_canonical_json(document))

    except FileNotFoundError:
        click.secho(f"Error: File not found: {path}", fg="red", err=True)
        sys.exit(1)
    except AIDocError as e:
        click.secho(f"Processing Error: {e}", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"Unexpected error: {e}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

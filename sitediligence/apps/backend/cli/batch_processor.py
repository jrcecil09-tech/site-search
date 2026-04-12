"""CLI: run batch queries for a list of sites from a CSV/JSON file."""

import json
from pathlib import Path

import typer

app = typer.Typer(help="Batch process site queries from a file.")


@app.command()
def run(
    input_file: Path = typer.Argument(..., help="CSV or JSON file with site coordinates"),
    query_types: str = typer.Option("wetlands,flood_zones,epa", help="Comma-separated query types"),
    output_dir: Path = typer.Option(Path("./output"), help="Directory to write results"),
    dry_run: bool = typer.Option(False, help="Print plan without executing"),
):
    """Process a list of sites and run the specified queries for each."""
    output_dir.mkdir(parents=True, exist_ok=True)
    types = [q.strip() for q in query_types.split(",")]

    if not input_file.exists():
        typer.echo(f"Error: {input_file} not found", err=True)
        raise typer.Exit(1)

    typer.echo(f"Loading sites from {input_file}...")
    # TODO: parse CSV/JSON, dispatch async query_runner for each site
    typer.echo(f"Query types: {types}")
    typer.echo(f"Output: {output_dir}")
    if dry_run:
        typer.echo("[dry-run] No queries executed.")


if __name__ == "__main__":
    app()

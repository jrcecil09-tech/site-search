"""CLI: watch a folder for new GIS files and auto-ingest them."""

import time
from pathlib import Path

import typer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

app = typer.Typer(help="Watch a folder and auto-ingest new GIS files.")

SUPPORTED_EXTENSIONS = {".geojson", ".json", ".dxf", ".shp", ".kml", ".gpx"}


class GISFileHandler(FileSystemEventHandler):
    def __init__(self, site_id: str, api_url: str):
        self.site_id = site_id
        self.api_url = api_url

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            typer.echo(f"  → Detected: {path.name}")
            # TODO: call storage upload API, trigger geometry parsing
            typer.echo(f"    [TODO] Upload {path.name} to site {self.site_id}")


@app.command()
def watch(
    folder: Path = typer.Argument(..., help="Folder to watch for new GIS files"),
    site_id: str = typer.Option(..., help="Site ID to associate uploaded files with"),
    api_url: str = typer.Option("http://localhost:8000", help="Backend API base URL"),
):
    """Monitor a folder and ingest new GIS files as they appear."""
    if not folder.exists():
        typer.echo(f"Error: {folder} does not exist", err=True)
        raise typer.Exit(1)

    typer.echo(f"Watching: {folder.resolve()}")
    typer.echo(f"Site ID:  {site_id}")
    typer.echo(f"Formats:  {', '.join(SUPPORTED_EXTENSIONS)}")
    typer.echo("Press Ctrl+C to stop.\n")

    handler = GISFileHandler(site_id=site_id, api_url=api_url)
    observer = Observer()
    observer.schedule(handler, str(folder), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    app()

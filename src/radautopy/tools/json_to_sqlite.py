import json
from pathlib import Path

import click

from ..utils.config import CONFIG_DIR, DB_PATH, store


def port_json_dir(source_dir: Path, db_path: Path) -> tuple[int, list[str]]:
    imported = 0
    skipped = []
    for path in sorted(source_dir.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            skipped.append(f"{path.name}: {e}")
            continue

        store.save(path.name, data, db_path=db_path)
        imported += 1

    return imported, skipped


@click.command()
@click.option(
    "--source-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=CONFIG_DIR,
    show_default=True,
    help="Directory of *.json files to port",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path),
    default=DB_PATH,
    show_default=True,
    help="SQLite database file to write to (created if missing)",
)
def main(source_dir: Path, db_path: Path) -> None:
    """One-time port of a directory of JSON files into the SQLite database radautopy now reads/writes from."""
    imported, skipped = port_json_dir(source_dir, db_path)
    click.echo(f"Imported {imported} file(s) into {db_path}")
    if skipped:
        click.echo(f"Skipped {len(skipped)} file(s):")
        for line in skipped:
            click.echo(f"  {line}")


if __name__ == "__main__":
    main()

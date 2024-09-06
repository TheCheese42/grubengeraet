import argparse
import sys
import tomllib
from pathlib import Path

from . import miner


def get_predefined_url(name: str) -> str:
    path = (
        Path(__file__).resolve().parent.parent.parent / "predefined_urls.toml"
    )
    with open(path, mode="rb") as fp:
        return tomllib.load(fp)[name.upper()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Grubengerät-miner",
        description="Ein Webminer für das UnlimitedWorld.de Forum.",
        epilog="Vergiss nicht auf uwmc.de zu spielen.",
    )

    parser.add_argument(
        "-u",
        "--url",
        action="store",
        default="",
        type=str,
        required=False,
        help="Basis URL eines Threads.",
        dest="url",
    )
    parser.add_argument(
        "-pd",
        "--pre-defined",
        action="store",
        default="",
        type=str,
        required=False,
        help="Wähle eine Vordefinierte URL aus.",
        dest="predefined",
    )
    parser.add_argument(
        "-p",
        "--path",
        action="store",
        default=Path.cwd() / ".html_content",
        type=Path,
        required=False,
        help="Ordner zum Speichern der heruntergeladenen HTML Dateien.",
        dest="path",
    )
    parser.add_argument(
        "-n",
        "--new-pages-only",
        action="store_true",
        required=False,
        help="Lade nur Seiten, die noch nicht im Zielverzeichnis vorhanden "
             "sind. Alte Seiten, die verändert wurden werden nicht erneuert.",
        dest="new_pages_only",
    )
    parser.add_argument(
        "-t",
        "--threaded",
        action="store_true",
        default=False,
        required=False,
        help="Lädt alle Seiten parallel. Erhöht Geschwindigkeit meist "
             "drastisch.",
        dest="threaded",
    )
    parser.add_argument(
        "-cs",
        "--chunk-size",
        action="store",
        default=20,
        type=int,
        required=False,
        help="Chunk Größe für parallele Downloads. 0 für so viele Chunks wie Seiten.",
        dest="chunk_size",
    )
    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        default=False,
        required=False,
        help="Debug Meldungen werden unterdrückt.",
        dest="silent",
    )

    args = parser.parse_args()
    miner.set_verbose(not args.silent)  # type: ignore
    # mypy bug, shows missing attribute of miner although it's there.
    # Happened multiple times, therefore multiple `# type: ignore` lines.

    if not args.url and not args.predefined:
        print("Weder --url, noch --pre-defined sind angegeben.")
        sys.exit(1)
    if args.url and args.predefined:
        print("Nur --url ODER --pre-defined darf angegeben sein.")
        sys.exit(1)

    if args.predefined:
        try:
            args.url = get_predefined_url(args.predefined)
        except ValueError:
            print("Die Vordefinierte URL `{args.predefined}` existiert nicht.")
            sys.exit(1)

    if not args.url.endswith("/"):
        args.url += "/"

    if not args.path.exists():
        print(f"Der angegebene Pfad existiert nicht: {args.path}")
        sys.exit(1)
    if not args.path.is_dir():
        print(f"Der angegebene Pfad ist kein Verzeichnis: {args.path}")
        sys.exit(1)

    try:
        if args.threaded:
            print(
                f"Paralleles Laden: Aktiviert (Chunk size: {args.chunk_size})"
            )
            if args.new_pages_only:
                print("Nur neue Seiten: Aktiviert.")
                miner.fetch_new_pages(  # type: ignore
                    args.url, working_dir=args.path, threaded=args.threaded
                )
            else:
                miner.fetch_and_save_all_pages_concurrently(
                    base_url=args.url,
                    working_dir=args.path,
                    chunk_size=args.chunk_size,
                )
        else:
            print("Paralleles Laden: Deaktiviert.")
            if not args.silent:
                print("Um den Prozess zu beschleunigen, benutze die "
                      "--threaded flag.")
            if args.new_pages_only:
                print("Nur neue Seiten: Aktiviert.")
                miner.fetch_new_pages(  # type: ignore
                    args.url, working_dir=args.path, threaded=args.threaded
                )
            else:
                miner.fetch_and_save_all_pages_linearly(
                    base_url=args.url,
                    working_dir=args.path,
                )
    except KeyboardInterrupt:
        print("Abgebrochen wegen KeyboardInterrupt.")
        sys.exit(1)

    print(
        f"{miner.get_last_page(args.url)} Seiten wurden nach "
        f"{args.path.resolve()} gespeichert."
    )

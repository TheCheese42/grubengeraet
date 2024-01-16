import argparse
import sys
from pathlib import Path

import miner

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
        required=True,
        help="Basis URL eines Threads.",
        dest="url",
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
        "--threaded",
        action="store_true",
        default=False,
        required=False,
        help="Lädt alle Seiten parallel. Erhöht Geschwindigkeit meist "
             "drastisch.",
        dest="threaded",
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

    if not args.url.endswith("/"):
        args.url += "/"

    try:
        if args.threaded:
            print("Paralleles Laden: Aktiviert.")
            if args.new_pages_only:
                print("Nur neue Seiten: Aktiviert.")
                miner.fetch_new_pages(  # type: ignore
                    args.url, working_dir=args.path, threaded=args.threaded
                )
            else:
                miner.fetch_and_save_all_pages_concurrently(
                    base_url=args.url, working_dir=args.path
                )
        else:
            print("Paralleles Laden: Deaktiviert.")
            if not args.silent:
                print("Um den Prozess zu beschleunigen, benutze die --silent "
                      "flag.")
            if args.new_pages_only:
                print("Nur neue Seiten: Aktiviert.")
                miner.fetch_new_pages(  # type: ignore
                    args.url, working_dir=args.path, threaded=args.threaded
                )
            miner.fetch_and_save_all_pages_linearly(
                base_url=args.url,
                working_dir=args.path,
            )
    except KeyboardInterrupt:
        print("Abgebrochen wegen KeyboardInterrupt.")
        sys.exit(1)

    print(
        f"{miner.get_last_page(args.url)} wurden nach "
        f"{args.path.resolve()} gespeichert."
    )

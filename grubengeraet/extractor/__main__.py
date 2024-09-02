import argparse
import multiprocessing
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import scraper


def parse_range(rangestring: str) -> range:
    """Parses a special range string.

    Args:
        rangestring (str): A string with format `"n1,n2,n3"`, where n2 is
        exclusive and n3 optional.

    Returns:
        range: The range object to produce.
    """
    parts = rangestring.split(",")
    if len(parts) not in (2, 3):
        raise ValueError("Invalid rangestring")
    nums = [int(i) for i in parts]
    return range(*nums)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Grubengerät-extractor",
        description="Ein Datenverarbeiter für das UnlimitedWorld.de Forum.",
        epilog="Vergiss nicht auf uwmc.de zu spielen.",
    )

    parser.add_argument(
        "-p",
        "--path",
        action="store",
        default=Path.cwd() / ".html_content",
        type=Path,
        required=False,
        help="Ordner, der die HTML Seiten eines Threads enthält.",
        dest="path",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        default="",
        type=str,
        required=False,
        help="Ausgabedatei für die Extrahierten Daten im JSON Format. "
             "Standartmäßig werden diese nach stdout ausgegeben.",
        dest="output",
    )
    parser.add_argument(
        "--pagerange",
        action="store",
        type=str,
        required=False,
        help="Eine Range von Seiten, die analysiert werden soll. Sie sollte "
             "das Format \"n1,n2,n3\" haben. n2 ist exklusiv, n3 ist "
             "optional. Nur eine *range flag ist erlaubt.",
        dest="pagerange",
    )
    parser.add_argument(
        "--postrange",
        action="store",
        type=str,
        required=False,
        help="Eine Range von Beiträgen, die analysiert werden soll. Sie "
             "sollte das Format \"n1,n2,n3\" haben. n2 ist exklusiv, n3 ist "
             "optional. Nur eine *range flag ist erlaubt.",
        dest="postrange",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        action="store",
        type=int,
        required=False,
        default=1,
        help="Anzahl der Unterprozesse, die zum extrahieren verwendet werden "
             "sollen. 1 erstellt keine Unterprozesse. 0 oder negativ erstellt "
             "so viele Prozesse, wie Kerne (inkl. hyperthreads) verfügbar "
             "sind.",
        dest="jobs",
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

    if args.pagerange and args.postrange:
        print("Nur eine *range flag ist erlaubt.")
        sys.exit(1)

    range_arg = {}
    if args.pagerange:
        range_arg["pagerange"] = parse_range(args.pagerange)
    if args.postrange:
        range_arg["postrange"] = parse_range(args.postrange)

    try:
        if args.jobs == 1:
            df = scraper.construct_dataframe(
                args.path,
                **range_arg,
                silent=args.silent,
            )
        else:
            if args.jobs < 1:
                jobs = os.cpu_count() or 1
            else:
                jobs = args.jobs
            processes: list[multiprocessing.Process] = []
            queue = multiprocessing.Queue()
            full_page_range = [
                int(re.findall(r"\d+", file.name)[0]) for file in sorted(
                    Path(args.path).iterdir(), key=lambda s: re.findall(
                        r"\d+", s.name)[0]) if file.is_file()]
            chunks = np.array_split(
                range_arg.get("pagerange")
                or range_arg.get("postrange")
                or full_page_range,
                jobs,
            )
            # Filter empty chunks
            chunks = [chunk for chunk in chunks if chunk.size > 0]
            jobs = min(jobs, len(chunks))
            if not args.silent:
                print(f"Processing using {jobs} jobs.")
            with multiprocessing.Pool() as pool:
                iterable = []
                for chunk in chunks:
                    iterable.append(
                        [args.path,
                         chunk.tolist() if not range_arg.get("postrange")
                         else None,
                         chunk.tolist() if range_arg.get("postrange")
                         else None,
                         args.silent]
                    )
                dfs = pool.starmap(scraper.construct_dataframe, iterable)
            df = pd.concat(dfs, ignore_index=True)
            df = df.sort_values(by="post_num")
    except FileNotFoundError:
        print("Ungültiger Pfad angegeben (Standart ist `.html_content` in "  # cspell:ignore Standart  # noqa
              "cwd)")
        sys.exit(1)

    if not args.output:
        print(df.to_json())
    else:
        path = Path(args.output)
        if path.is_dir():
            print("Der angegebene Pfad ist ein Verzeichnis.")
            sys.exit(1)
        df.to_json(path)

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas
from ..extractor import scraper
from matplotlib import pyplot as plt

from . import visualizer


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
        prog="Grubengerät-visualizer",
        description="Ein Visualisierer für das UnlimitedWorld.de Forum.",
        epilog="Vergiss nicht auf uwmc.de zu spielen.",
    )

    visualization_format_options = [
        i for i in dir(visualizer.DataVisualizer) if not i.startswith("_")
    ]
    visualization_format_options_str = ""
    for i in visualization_format_options:
        visualization_format_options_str += f"`{i}`, "
    visualization_format_options_str = visualization_format_options_str[:-2]

    parser.add_argument(
        "-p",
        "--path",
        action="store",
        type=Path,
        required=True,
        help="JSON Datei mit den extrahierten Daten.",
        dest="path",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        default="",
        type=str,
        required=False,
        help="Ausgabedatei für die generierten Visualisierungen. "
             "Visualisierungen, die als printable markiert sind, kommen utf-8 "
             "codiert in eine Textdatei. Alle, die als plot markiert sind, "
             "gehören in eine binäre Bilddatei.\n"
             "Standartmäßig werden printable Visualisierungen zum stdout "
             "ausgegeben, plots werden im show tool von Matplotlib angezeigt.",
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
        "-f",
        "--format",
        action="store",
        type=str,
        required=True,
        help="Die Visualisierungsfunktion, die benutzt werden soll. "
             f"Mögliche Optionen:\n{visualization_format_options_str}",
        dest="format",
    )
    parser.add_argument(
        "-fo",
        "--format-options",
        action="store",
        type=str,
        required=False,
        help="Optionen, die zur Visualisierungsfunktion übergeben werden. "
             "Sollte das Format \"arg1:value1;arg2:value2:argN:valueN\" "
             "haben.",
        dest="format_options",
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
        df = pandas.read_json(args.path)
    except FileNotFoundError:
        print(f"The file {args.path} does not exist.")
        sys.exit(1)
    except pandas.errors.ParserError:
        print(f"The file {args.path} is not a valid JSON file.")
        sys.exit(1)
    if list(df.columns) != scraper.COLUMNS:
        print(f"The JSON file {args.path} was not generated using this "
              "version of Grubengerät.")
        sys.exit(1)

    visualizer = visualizer.DataVisualizer(
        data_extractor=visualizer.DataExtractor(df)
    )
    try:
        method = getattr(visualizer, args.format)
    except AttributeError:
        print("Invalid visualization method. Use --help to get a list of "
              "valid methods.")
        sys.exit(1)
    parameters: dict[str, Any] = {}
    if args.format_options:
        options = args.format_options.split(";")
        for i in options:
            if ":" not in i:
                print("Invalid format options provided.")
                sys.exit(1)
            option: list[Any] = i.split(":")
            if option[1].isdigit():
                option[1] = int(option[1])
            elif option[1].replace(".", "", 1).isdigit():
                option[1] = float(option[1])
            parameters[option[0]] = option[1]

    visualization = method(**parameters)
    if method.__doc__.strip().startswith("<printable>"):
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as fp:
                    fp.write(visualization)
            except (PermissionError, OSError):
                print(f"Cannot write to file {args.output}!")
                sys.exit(1)
        else:
            print(visualization)
    elif method.__doc__.strip().startswith("<plot>"):
        if args.output:
            try:
                visualization.savefig(args.output, bbox_inches='tight')
                plt.close(visualization)
            except (PermissionError, OSError):
                print(f"Cannot write to file {args.output}!")
                sys.exit(1)
        else:
            plt.show(block=True)

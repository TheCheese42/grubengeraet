# Grubengerät
Web scraper und Statistiker für das UnlimitedWorld.de Forum.

# Installation

Linux/MacOS:

```sh
git clone https://github.com/NotYou404/grubengeraet/
cd grubengeraet
python -m venv .venv
src .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows:

```pwsh
git clone https://github.com/NotYou404/grubengeraet/
cd grubengeraet
python -m venv .venv
.venv/bin/activate.ps1
python -m pip install -r requirements.txt
```

# Benutzung

## Miner

Zuerst müssen die HTML Seiten heruntergeladen werden.
Für alle Optionen siehe `python -m grubengeraet.miner -h`.

Beispiel:

```sh
python -m grubengeraet.miner --url https://unlimitedworld.de/threads/wer-als-letztes-antwortet-kriegt-viel-mehr-als-nur-128-dias.8439/ --threaded
```

Oder:

```sh
python -m grubengeraet.miner --pre-defined wala --threaded
```

Die Seiten landen standartmäßig im `.html_content` Verzeichnis.

## Extractor

Danach werden die Daten extrahiert und in eine CSV Datei gepackt.
Für alle Optionen siehe `python -m grubengeraet.extractor -h`.

Beispiel:

```sh
python -m grubengeraet.extractor --output data.csv
```

Nun sind alle wichtigen Daten in der `data.csv` Datei gesammelt.

## Visualizer

Zuletzt müssen die erarbeiteten Daten Visualisiert werden.
Für alle Optionen siehe `python -m grubengeraet.visualizer -h`.

Beispiel:

```sh
python -m grubengeraet.visualizer --path data.csv --output table.txt --format maua1_style_bbtable
```

Oder für Plots:

```sh
python -m grubengeraet.visualizer --path data.csv --output plot.svg --format some_sample_plot_function
```

Das Format des Plots passt sich der angegebenen Dateiendung an. Auch Vektorbasierte Formate wie SVG werden unterstützt.

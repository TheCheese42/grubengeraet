# Grubengerät

Web scraper und Statistiker für das UnlimitedWorld.de Forum.

## Installation

Linux/MacOS:

```sh
git clone https://github.com/NotYou404/grubengeraet/
cd grubengeraet
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Windows:

```sh
git clone https://github.com/NotYou404/grubengeraet/
cd grubengeraet
python -m venv .venv
.venv/Scripts/activate.ps1
python -m pip install -r requirements.txt
```

## Benutzung

### Miner

Zuerst müssen die HTML Seiten heruntergeladen werden.
Für alle Optionen siehe `python -m grubengeraet.miner -h`.

Die Standartgröße der Chunks beim parallelen Download beträgt 20. Wird sie auf 0 gesetzt (`--chunk-size 0`) werden **alle** Seiten gleichzeitig geladen.

Beispiel:

```sh
python -m grubengeraet.miner --url https://unlimitedworld.de/threads/wer-als-letztes-antwortet-kriegt-viel-mehr-als-nur-128-dias.8439/ --threaded
```

Oder:

```sh
python -m grubengeraet.miner --pre-defined wala --threaded
```

Die Seiten landen standartmäßig im `.html_content` Verzeichnis.

Durch das weglassen der `--threaded` flag werden die Seiten linear, nacheinander heruntergeladen. Dies dauert bei großen Threads aber sehr lange.

### Extractor

Danach werden die Daten extrahiert und in einer JSON Datei gespeichert.
Für alle Optionen siehe `python -m grubengeraet.extractor -h`.

Beispiel:

```sh
python -m grubengeraet.extractor --output data.json
```

Nun sind alle wichtigen Daten in der `data.csv` Datei gesammelt.

Alternativ kann auch nur ein bestimmter Bereich analysiert werden. Dies wird mit den `--pagerange` und `--postrange` Funktionen erreicht. Sie müssen in Anführungszeichen übergeben werden und haben das format `"start,stop,step"`, wobei `stop` exklusiv und `step` optional ist.

Beispiel:

```sh
python -m grubengeraet.extractor --output data.json --pagerange "100,1001"
```

Hier werden nur Beiträge, die auf den Seiten 100 bis 1000 liegen berücksichtigt.

### Visualizer

Zuletzt müssen die erarbeiteten Daten Visualisiert werden.
Für alle Optionen siehe `python -m grubengeraet.visualizer -h`.

Beispiel:

```sh
python -m grubengeraet.visualizer --path data.json --output table.txt --format maua1_style_bbtable
```

Oder für Plots:

```sh
python -m grubengeraet.visualizer --path data.json --output plot.svg --format some_sample_plot_function
```

Das Format des Plots passt sich der angegebenen Dateiendung an. Auch Vektor-basierte Formate wie SVG werden unterstützt.

# Grubengerät

Web scraper und Statistiker für das UnlimitedWorld.de Forum.

## Installation

Linux/MacOS:

```sh
git clone https://github.com/TheCheese42/grubengeraet/
cd grubengeraet
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Windows:

```sh
git clone https://github.com/TheCheese42/grubengeraet/
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
python -m grubengeraet.visualizer --path data.json --output plot.svg --format top_n_pie
```

Das Format des Plots passt sich der angegebenen Dateiendung an. Auch Vektor-basierte Formate wie SVG werden unterstützt.

## Visualizer Docs

Die Visualisierungsfunktion wird mit `--format` angegeben. Dazu gibt es jeweils noch Optionen, die mit `--format-options` (`-fo`) angegeben werden können, im Format `"arg1:value1;arg2:value2;arg3:value3"`.

Beispiel:

```sh
python -m grubengeraet.visualizer --path data.json --output plot.svg --format top_n_pie --format-options "n:20;criterion:words"
```

Hier werden die ersten 20 (`n:20`) Autoren mit den meisten geschriebenen Wörtern (`criterion:words`) in einem Kuchendiagramm dargestellt.

### Text-basiert

#### maua1_style_bbtable

Gibt eine BBCode Tabelle aus, die alle Autoren mit der Anzahl Beiträgen, Regelbrüchen, sowie Prozentsatz der ungültigen Beiträge enthält.

Keine Optionen.

#### rule_violation_bbtable_np

Gibt eine BBCode Tabelle aus, die alle Autoren mit der Anzahl Beiträgen, Regelbrüchen, sowie Prozentsatz der ungültigen Beiträge enthält, sortiert nach dem Prozentsatz der Regelbrüche, aufsteigend.

`n`: Anzahl Nachrichten, die benötigt sind, um in der Tabelle aufzutauchen.

#### emoji_frequency_bbtable

Gibt eine BBCode Tabelle aus, mit allen auftretenden Emojis sortiert nach Häufigkeit. Beachte, dass viele Forensoftwares nicht alle Unicode Emojis anzeigen können.

### Grafisch

#### top_n_pie

Ein Kuchendiagramm, das die Top n Autoren darstellt, entweder anhand von Beiträgen oder Wörtern.

`n`: Anzahl Personen, die dargestellt werden sollen.
`criterion`: `messages` oder `words`.
`radius`: Radius des Diagramms.

#### yearly_top_n_barh_percent

Ein horizontales Balkendiagramm pro Jahr, zeigt die Top Autoren in Sachen Beiträge oder Wörter.

`n`: Anzahl Personen, die dargestellt werden sollen.
`criterion`: `messages`oder `words`.

#### emojis_pie_top_n

Kuchendiagramm, das die Top n Emojis anhand ihrer Häufigkeit angibt.

`n`: Anzahl gezeigter Emojis.

#### emoji_distribution_top_n

Balkendiagramm mit den Top n Emoji-Autoren, und welche Emojis diese wie oft verwendet haben.

`n`: Anzahl Personen, die dargestellt werden sollen.
`n_emojis`: Anzahl Emojis, die in der Legende angezeigt werden sollen.

#### top_n_mentioned_barh

Horizontales Balkendiagramm, das die Top n meist gepingten Forennutzer zeigt.

`n`: Anzahl Personen, die dargestellt werden sollen.

#### top_n_mentions_barh

Horizontales Balkendiagramm, das die Top n Autoren mit den meisten Pings zeigt.

`n`: Anzahl Personen, die dargestellt werden sollen.

#### top_n_quoted_barh

Horizontales Balkendiagramm, das die Top n meist zitierten Forennutzer zeigt.

`n`: Anzahl Personen, die dargestellt werden sollen.

#### top_n_quotes_barh

Horizontales Balkendiagramm, das die Top n Autoren mit den meisten Zitaten zeigt.

`n`: Anzahl Personen, die dargestellt werden sollen.

#### prediction_line

Liniendiagramm, mit dem ein Trend visualisiert wird. Es wird vorhergesagt, wann ein besagtes Ziel erreicht wird, anhand eines gewissen Zeitraums.

`goal`: Das Ziel an Beiträgen (z.B. 25000). (Pflicht)
`data_period_start`: Der Beginn des Zeitraums. (Pflicht)
`data_period_end`: Das Ende des Zeitraums. (Pflicht)
`data_period_type`: Was die oberen beiden Parameter angeben. Eins von `post`, `page` oder `timestamp`. (Pflicht)
`description`: Eine Beschreibung, die an den Titel angehängt werden soll (z.B. `(anhand der letzten 30 Tage)`).

#### authors_per_year_bar

Vertikales Balkendiagramm, das die Anzahl verschiedener Teilnehmer eines Threads pro Jahr darstellt.

#### posts_per_author_per_year_bar

Vertikales Balkendiagramm, das die Anzahl Nachrichten pro Teilnehmer pro Jahr darstellt.

#### top_n_words_per_message_bar

Horizontales Balkendiagramm, das die Top n Autoren in Sachen Wörter pro Beitrag darstellt.

`n`: Anzahl Autoren, die dargestellt werden sollen.

#### letter_occurrences_barh

Horizontales Balkendiagramm, das Zeichen sortiert nach Häufigkeit angibt.

`mode`: Wie soll gezählt werden: `count_all` - Einfach alle Zeichen, die in Wörtern vorkommen (Satzzeichen sind hier normal nicht dabei), zählen. `count_first` - Alle Zeichen am Wortanfang zählen. `count_last` - Alle Zeichen am Wortende zählen. Standartmäßig `count_all`.
`chars`: Ein string aller Charaktere, die gezählt werden sollen. Standartmäßig a-z, sowie äöüß.
`case_insensitive`: Ob Groß- und Kleinbuchstaben getrennt gezählt werden sollen. Standartmäßig True.

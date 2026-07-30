# Pygrator — CSV Data Mapper & Schema Validator

**Pygrator** ist eine intuitive Desktop-Anwendung mit einer modernen Grafischen Benutzeroberfläche (GUI) auf Basis von Python und `customtkinter`.<br>
Sie dient der Transformation, Bereinigung, Validierung und Konvertierung von CSV-Datenbeständen in vordefinierte Datenbank-Zielschemata (z. B. für Patienten- oder Adressdatenbanken).

---

## 📋 Inhaltsverzeichnis

* [Pygrator — CSV Data Mapper & Schema Validator](https://www.google.com/search?q=%23pygrator--csv-data-mapper--schema-validator)
  * [📋 Inhaltsverzeichnis](https://www.google.com/search?q=%23-inhaltsverzeichnis)
  * [✨ Features](https://www.google.com/search?q=%23-features)
  * [📁 Projektstruktur](https://www.google.com/search?q=%23-projektstruktur)
  * [⚙️ Voraussetzungen & Installation](https://www.google.com/search?q=%23%EF%B8%8F-voraussetzungen--installation)
    * [Voraussetzungen](https://www.google.com/search?q=%23voraussetzungen)
    * [Installation](https://www.google.com/search?q=%23installation)
  * [🚀 Schnellstart](https://www.google.com/search?q=%23-schnellstart)
    * [📖 Anleitung & Funktionsweise](https://www.google.com/search?q=%23-anleitung--funktionsweise)
    * [1. Quelldatei laden](https://www.google.com/search?q=%231-quelldatei-laden)
    * [2. Zielschema wählen](https://www.google.com/search?q=%232-zielschema-w%C3%A4hlen)
    * [3. Spalten-Zuordnung (Mapping)](https://www.google.com/search?q=%233-spalten-zuordnung-mapping)
    * [4. Transformations- & Validierungsregeln anwenden](https://www.google.com/search?q=%234-transformations--und-validierungsregeln-anwenden)
    * [5. Pre-Check Export (Vorab-Inspektion)](https://www.google.com/search?q=%235-pre-check-export-vorab-inspektion)
    * [6. Feldlängen-Konflikte lösen (VARCHAR-Check)](https://www.google.com/search?q=%236-feldl%C3%A4ngen-konflikte-l%C3%B6sen-varchar-check)
    * [7. Export & Restdatei-Sicherung](https://www.google.com/search?q=%237-export--restdatei-sicherung)


  * [🛠️ Verfügbare Transformations- & Validierungsregeln](https://www.google.com/search?q=%23%EF%B8%8F-verf%C3%BCgbare-transformations--und-validierungsregeln)
  * [📐 Eigene Schemata hinzufügen (`schemas.py`)](https://www.google.com/search?q=%23-eigene-schemata-hinzuf%C3%BCgen-schemaspy)
  * [📄 Lizenz & Mitwirkung](https://www.google.com/search?q=%23-lizenz--mitwirkung)


---
## ✨ Features

* 🔍 **Automatische Dateierkennung**: Erkennt Trennzeichen (Semikolon, Komma, Tabulator) sowie Encodings (`UTF-8`, `UTF-8-BOM`, `CP1252`, `Latin-1`) automatisch.
* 🎯 **Dynamisches Schema-Mapping**: Grafische Zuordnung von CSV-Quelldateien zu festen Datenbank-Tabellenstrukturen.
* 🕵️ **Smarte Vorab-Inspektion (Pre-Check Export)**:
  * Prüft **ausschließlich zugewiesene Zielspalten** auf Fehler (nicht gemappte Freitextspalten wie *Notiz* werden ignoriert).
  * Evaluiert Längenbegrenzungen **erst nach Anwendung** von Regellogiken (z. B. wird eine Hausnummer erst extrahiert und dann gegen das Limit geprüft).
  * Erstellt eine detaillierte Kontroll-CSV inkl. Quell-Zeilennummer und exakter Fehlerbeschreibung (`__gefundene_fehler`).


* 🛠️ **Mächtige Transformations- & Validierungsregeln**:
* **KVNR Auto-Korrektur (`validate_kvnr`)**: Erkennt typische OCR-/Eingabefehler bei Krankenversichertennummern (z. B. Verwechslung von `0` und `O` am Anfang) und stellt gültige KVNRs automatisch wieder her.
* **IK-Nummern-Validierung (`validate_ik`)**: Prüft Institutionskennzeichen nach der Prüfziffern-Logik der Gesetzlichen Krankenversicherung.
* **E-Mail-Validierung (`validate_email`)**: Identifiziert syntaktisch fehlerhafte E-Mail-Adressen.
* **Straße & Hausnummer trennen**: Extrahiert Straßenname oder Hausnummer zuverlässig – inklusive intelligenter Fallback-Logik für Straßen ohne Hausnummer (z. B. *"Auf den Hüllen"*).
* **UID-Generierung**: Erzeugt eindeutige, kompakte Base36-IDs basierend auf Zeitstempeln.
* **Datumsformatierung**: Konvertiert uneinheitliche Datumsformate (`DD.MM.YYYY`, `YYYY/MM/DD`, etc.) zuverlässig in das ISO-Format `YYYY-MM-DD`.
* **PLZ-Bereinigung**: Entfernt Fließkomma-Reste (`.0`) und füllt Postleitzahlen automatisch auf 5 Stellen auf.
* **Geschlechts-Normalisierung**: Konvertiert Kürzel (`M`/`W`/`F`) in Anreden (`Herr`/`Frau`).
* **Zwei Spalten verknüpfen**: Verknüpft zwei Quellspalten mit Leerzeichen in einer Zielspalte.
* **Sonderzeichen-Bereinigung**: Säubert unerwünschte Zeichen in Namen und Freitexten.


* ⚠️ **Zellgenaue VARCHAR-Längenprüfung**: Erkennt Überschreitungen von Datentyp-Begrenzungen im Zielschema und bietet einen Dialog zur Einzel- oder Massenbearbeitung.
* 🛡️ **Ungemappte Spalten sichern**: Speichert alle nicht zugewiesenen Quellspalten automatisch in einer separaten Restdatei (`REST_UNMAPPED_...csv`), damit keine Daten verloren gehen.
* 🎨 **Moderne Benutzeroberfläche**: Basiert auf CustomTkinter mit automatischer Hell-/Dunkelmodus-Anpassung.

---

## 📁 Projektstruktur

```text
.
├── pygrator.py     # Hauptprogramm (CustomTkinter GUI, Vorab-Inspektion & Export-Logik)
├── db_util.py      # Hilfsfunktionen (KVNR-Fixing, IK-/KVNR-Validierung, Sonderzeichen, IDs)
├── schemas.py      # Definition der Zielschemata und Datentypen (z. B. patienten, adressen)
```

---

## ⚙️ Voraussetzungen & Installation

### Voraussetzungen

* Python **3.10** oder neuer
* Betriebssystem: Windows, macOS oder Linux

### Installation

1. **Repository klonen oder Projektordner öffnen:**
```bash
git clone https://github.com/tgbox/pygrator.git
cd pygrator
```

2. **Virtuelle Umgebung erstellen (optional, aber empfohlen):**
```bash
python -m venv .venv
# Unter Windows aktivieren:
.venv\Scripts\activate
# Unter macOS/Linux aktivieren:
source .venv/bin/activate
```

3. **Erforderliche Abhängigkeiten installieren:**
```bash
pip install -r ./requirements.txt
```

---

## 🚀 Schnellstart

Starte die Anwendung einfach über das Terminal:

```bash
python ./pygrator.py
```

---

## 📖 Anleitung & Funktionsweise

### 1. Quelldatei laden

Klicke oben links auf **„Quelldatei laden (CSV)“** und wähle deine CSV- oder TXT-Datei aus. Die App erkennt automatisch das Trennzeichen und die Zeichenkodierung.

### 2. Zielschema wählen

Wähle aus dem Dropdown-Menü **„Zielschema“** die Zielstruktur der Datenbank aus (z. B. `patienten` oder `adressen`).

### 3. Spalten-Zuordnung (Mapping)

Die App ordnet Quellspalten anhand Namensgleichheit und einiger weiterer vorab definierter Regeln automatisch zu. Du kannst die Dropdown-Menüs in der Spalte **„Quellspalte (CSV)“** manuell anpassen oder auf `-- Nicht zuordnen / Spezielle Regel --` stellen.

### 4. Transformations- und Validierungsregeln anwenden

Klicke neben einer Zielspalte auf **„Regel hinzufügen...“**, um eine erweiterte Transformation oder Validierung festzulegen:

* **Adressen trennen:** Setze für `p_street` die Regel *„Straße/Hausnr. trennen -> Nur Text“* und für `p_hausnummer` die Regel *„Straße/Hausnr. trennen -> Nur Nummer“*.
* **Versichertennummer prüfen/bereinigen:** Weise der KVNR-Zielspalte die Regel `validate_kvnr` zu.

### 5. Pre-Check Export (Vorab-Inspektion)

Klicke auf **„Pre-Check Export“**, um deine Daten vor dem endgültigen Export auf Herz und Nieren zu prüfen:

* Es werden **nur Spalten evaluiert**, die tatsächlich einem Zielfeld zugeordnet sind.
* Fehlerhafte Zeilen werden in eine CSV-Datei exportiert, in der die exakte Zeilennummer der Quelldatei sowie alle gefundenen Fehler (Überlängen, ungültige KVNR/IK, Sonderzeichen) übersichtlich aufgelistet sind.

### 6. Feldlängen-Konflikte lösen (VARCHAR-Check)

Beim Ausführen des Haupt-Exports prüft die Anwendung alle finalen Werte gegen das Datentyp-Limit des Zielschemas (z. B. `VARCHAR(40)`). Bei Überschreitungen öffnet sich ein Korrektur-Dialog:

* **Alle automatisch kürzen**: Schneidet überlange Werte am Limit ab.
* **Eigener Wert**: Ermöglicht manuelle Korrekturen pro Zeile.
* **Unverändert belassen**: Ignoriert die Warnung für ausgewählte Werte.

### 7. Export & Restdatei-Sicherung

Nach der Bestätigung wählst du den Speicherort der verarbeiteten CSV-Datei aus. Ist das Kontrollkästchen *„Rest-Datei für ungemappte Spalten erstellen“* aktiviert, wird im selben Ordner eine Sicherung aller verbliebenen Quellspalten angelegt.

---

## 🛠️ Verfügbare Transformations- & Validierungsregeln

| Regel | Kategorie | Beschreibung | Beispiel / Anwendungsfall |
| --- | --- | --- | --- |
| 🛡️ **`validate_kvnr`** | Validierung | Behebt O/0-Verwechslungen (`try_to_fix_insurance_number`) & prüft KVNR-Format. | `0123456789` ➔ `O123456789` |
| 🛡️ **`validate_ik`** | Validierung | Prüft Institutionskennzeichen (9-stellig) nach Prüfziffern-Algorithmus. | `123456789` (Valide) |
| ✉️ **`validate_email`** | Validierung | Identifiziert fehlerhafte Mail-Syntax. | `user@domain` ➔ Flagged |
| 🏠 **Straße trennen** | Extraktion | Extrahiert nur den Straßennamen (fällt bei fehlender Hausnummer auf den Volltext zurück). | `Auf den Hüllen` ➔ `Auf den Hüllen` |
| 🔢 **Hausnummer trennen** | Extraktion | Extrahiert nur die Hausnummer (gibt einen leeren String zurück, falls keine Nummer existiert). | `Im Tiergarten 19` ➔ `19` |
| 🔗 **Spalten verknüpfen** | Transformation | Fügt zwei Quellspalten mit Leerzeichen zusammen. | `Musterstr.` + `4` ➔ `Musterstr. 4` |
| 📮 **PLZ bereinigen** | Bereinigung | Entfernt `.0` und füllt auf 5 Stellen auf. | `8033.0` ➔ `08033` |
| 👫 **Geschlecht mappen** | Mapping | Wandelt `M`/`W`/`F` um. | `M` ➔ `Herr`, `W` ➔ `Frau` |
| 📅 **Datumsformat** | Konvertierung | Konvertiert Werte zuverlässig in das Format `YYYY-MM-DD`. | `15.08.1985` ➔ `1985-08-15` |
| 🔑 **Neue UID generieren** | Generierung | Erzeugt eine eindeutige ID im Format `1K2J3X-A8F9B`. | Automatische Primärschlüssel |
| ✨ **Standardwert** | Fallback | Setzt Ersatzwert bei leeren Feldern. | Leere Zelle ➔ `Unbekannt` |
| 📌 **Statischer Festwert** | Konstante | Überschreibt alle Zeilen mit einem Festwert. | Statusspalte ➔ `AKTIV` |

---

## 📐 Eigene Schemata hinzufügen (`schemas.py`)

In der Datei `schemas.py` können beliebige weitere Zielstrukturen und Beschränkungen definiert werden:

```python
SCHEMAS = {
    "meine_tabelle": {
        "id": "VARCHAR(40)",
        "vorname": "VARCHAR(60)",
        "nachname": "VARCHAR(60)",
        "p_street": "VARCHAR(60)",
        "p_hausnummer": "VARCHAR(10)",
        "geburtsdatum": "DATE",
        "bemerkung": "TEXT"
    }
}
```

---

## 📄 Lizenz & Mitwirkung

Dieses Projekt steht unter der **MIT-Lizenz**. Beiträge, Issue-Meldungen und Feature-Wünsche sind herzlich willkommen!
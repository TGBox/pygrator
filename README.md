# Pygrator — CSV Data Mapper & Schema Validator

**Pygrator** ist eine intuitive Desktop-Anwendung mit einer modernen Grafischen Benutzeroberfläche (GUI) auf Basis von Python und `customtkinter`.<br>
Sie dient der Transformation, Bereinigung, Validierung und Konvertierung von CSV-Datenbeständen in vordefinierte Datenbank-Zielschemata (z. B. für Patienten- oder Adressdatenbanken).

---

## 📋 Inhaltsverzeichnis

- [Pygrator — CSV Data Mapper \& Schema Validator](#pygrator--csv-data-mapper--schema-validator)
  - [📋 Inhaltsverzeichnis](#-inhaltsverzeichnis)
  - [✨ Features](#-features)
  - [📁 Projektstruktur](#-projektstruktur)
  - [⚙️ Voraussetzungen \& Installation](#️-voraussetzungen--installation)
    - [Voraussetzungen](#voraussetzungen)
    - [Installation](#installation)
  - [🚀 Schnellstart](#-schnellstart)
  - [📖 Anleitung \& Funktionsweise](#-anleitung--funktionsweise)
    - [1. Quelldatei laden](#1-quelldatei-laden)
    - [2. Zielschema wählen](#2-zielschema-wählen)
    - [3. Spalten-Zuordnung (Mapping)](#3-spalten-zuordnung-mapping)
    - [4. Transformationsregeln anwenden](#4-transformationsregeln-anwenden)
    - [5. Feldlängen-Konflikte lösen (VARCHAR-Check)](#5-feldlängen-konflikte-lösen-varchar-check)
    - [6. Export \& Restdatei-Sicherung](#6-export--restdatei-sicherung)
  - [🛠️ Verfügbare Transformationsregeln](#️-verfügbare-transformationsregeln)
  - [📐 Eigene Schemata hinzufügen (`schemas.py`)](#-eigene-schemata-hinzufügen-schemaspy)
  - [📄 Lizenz \& Mitwirkung](#-lizenz--mitwirkung)

---

## ✨ Features

- 🔍 **Automatische Dateierkennung**: Erkennt Trennzeichen (Semikolon, Komma, Tabulator) sowie Encodings (`UTF-8`, `UTF-8-BOM`, `CP1252`, `Latin-1`) automatisch.
- 🎯 **Dynamisches Schema-Mapping**: Grafische Zuordnung von CSV-Quelldateien zu festen Datenbank-Tabellenstrukturen.
- 🛠️ **Mächtige Transformationsregeln**:
  - **UID-Generierung**: Erzeugt eindeutige, kompakte Base36-IDs basierend auf Zeitstempeln.
  - **Datumsformatierung**: Konvertiert uneinheitliche Datumsformate (`DD.MM.YYYY`, `YYYY/MM/DD`, etc.) zuverlässig in das ISO-Format `YYYY-MM-DD`.
  - **PLZ-Bereinigung**: Entfernt Fließkomma-Reste (`.0`) und füllt Postleitzahlen automatisch auf 5 Stellen auf.
  - **Geschlechts-Normalisierung**: Konvertiert Kürzel (`M`/`W`/`F`) in Anreden (`Herr`/`Frau`).
  - **Straße & Hausnummer trennen**: Extrahiert Straßenname oder Hausnummer aus einer kombinierten Adresse.
  - **Zwei Spalten verknüpfen**: Verknüpft zwei Quellspalten (z. B. `Straßenname` + `Hausnummer`) mit Leerzeichen in einer Zielspalte.
  - **Standard- & Statische Werte**: Setzt feste Werte oder füllt nur leere Felder mit konfigurierbaren Fallback-Werten auf.
  - **Zielspalten-Kopieren**: Übernimmt Daten aus bereits gemappten Zielspalten.
- ⚠️ **Zellgenaue VARCHAR-Längenprüfung**: Erkennt Überschreitungen von Datentyp-Begrenzungen und bietet einen Dialog zur Einzel- oder Massenbearbeitung (Kürzen, Eigener Wert, Ignorieren).
- 🛡️ **Ungemappte Spalten sichern**: Speichert alle nicht zugewiesenen Quellspalten automatisch in einer separaten Restdatei (`REST_UNMAPPED_...csv`), damit keine Daten verloren gehen.
- 🎨 **Moderne Benutzeroberfläche**: Basiert auf CustomTkinter mit automatischer Hell-/Dunkelmodus-Anpassung.

---

## 📁 Projektstruktur

```text
.
├── pygrator.py     # Hauptprogramm (CustomTkinter GUI & Transformations-Logik)
├── db_util.py      # Hilfsfunktionen zur Generierung eindeutiger IDs (Base36 + Timestamp)
├── schemas.py     # Definition der Zielschemata und Datentypen (z. B. patienten, adressen)
```

---

## ⚙️ Voraussetzungen & Installation

### Voraussetzungen
- Python **3.10** oder neuer
- Betriebssystem: Windows, macOS oder Linux

### Installation

1. **Repository klonen oder Projektordner öffnen:**
   ```bash
   git clone https://github.com/dein-user/pygrator.git
   cd pygrator
   ```

2. **Virtuelle Umgebung erstellen (optional, aber empfohlen):**
   ```bash
   python -m venv venv
   # Unter Windows aktivieren:
   venv\Scripts\activate
   # Unter macOS/Linux aktivieren:
   source venv/bin/activate
   ```

3. **Erforderliche Abhängigkeiten installieren:**
   ```bash
   pip install pandas customtkinter
   ```

---

## 🚀 Schnellstart

Starte die Anwendung einfach über das Terminal:

```bash
python pygrator.py
```

---

## 📖 Anleitung & Funktionsweise

### 1. Quelldatei laden
Klicke oben links auf **„Quelldatei laden (CSV)“** und wähle deine CSV- oder TXT-Datei aus. Die App erkennt automatisch das Trennzeichen und die Zeichenkodierung.

### 2. Zielschema wählen
Wähle aus dem Dropdown-Menü **„Zielschema“** die Zielstruktur der Datenbank aus (z. B. `patienten` oder `adressen`).

### 3. Spalten-Zuordnung (Mapping)
Die App ordnet Quellspalten anhand Namensgleichheit automatisch zu. Du kannst die Dropdown-Menüs in der Spalte **„Quellspalte (CSV)“** manuell anpassen oder auf `-- Nicht zuordnen / Spezielle Regel --` stellen.

### 4. Transformationsregeln anwenden
Klicke neben einer Zielspalte auf **„Regel hinzufügen...“**, um eine erweiterte Transformation festzulegen:
- **Beispiel Split:** Für `p_street` wählst du die Regel *„Straße/Hausnr. trennen -> Nur Text“*, für `p_hausnummer` die Regel *„Straße/Hausnr. trennen -> Nur Nummer“*.
- **Beispiel Merge:** Wenn deine Quelle getrennte Spalten für Straße und Hausnummer hat, deine Zieltabelle aber nur eine Spalte besitzt, wähle im Dropdown die erste Spalte aus und aktiviere im Regel-Dialog *„Zwei Quellspalten zusammenführen“* mit der zweiten Spalte.

### 5. Feldlängen-Konflikte lösen (VARCHAR-Check)
Nach einem Klick auf **„Prüfen & Exportieren“** prüft die Anwendung alle Werte gegen das Datentyp-Limit (z. B. `VARCHAR(40)`). Bei Überschreitungen öffnet sich ein Dialog:
- **Alle automatisch kürzen**: Schneidet überlange Werte am Limit ab.
- **Eigener Wert**: Ermöglicht manuelle Korrekturen pro Zeile.
- **Unverändert belassen**: Ignoriert die Warnung für ausgewählte Werte.

### 6. Export & Restdatei-Sicherung
Nach der Bestätigung wählst du den Speicherort der verarbeiteten CSV-Datei aus. Ist das Kontrollkästchen *„Rest-Datei für ungemappte Spalten erstellen“* aktiviert, wird im selben Ordner eine Sicherung aller verbliebenen Quellspalten angelegt.

---

## 🛠️ Verfügbare Transformationsregeln

| Regel | Beschreibung | Beispiel / Anwendungsfall |
| :--- | :--- | :--- |
| 🔑 **Neue UID generieren** | Erzeugt eine eindeutige ID im Format `1K2J3X-A8F9B` | Automatische Primärschlüssel-Generierung |
| 📅 **Datumsformat anpassen** | Konvertiert Werte in `YYYY-MM-DD` | `15.08.1985` ➔ `1985-08-15` |
| ✨ **Standardwert (nur leer)** | Setzt Ersatzwert bei leeren Feldern | Leere Zelle ➔ `Unbekannt` |
| 📌 **Statischer Festwert** | Überschreibt alle Zeilen mit einem Festwert | Statusspalte ➔ `AKTIV` |
| 🔗 **Wert aus Zielspalte** | Kopiert den Inhalt einer anderen Zielspalte | Rechnungsadresse = Lieferadresse |
| 📮 **PLZ bereinigen** | Entfernt `.0` und füllt auf 5 Stellen auf | `8033.0` ➔ `08033` |
| 👫 **Geschlecht mappen** | Wandelt `M`/`W`/`F` um | `M` ➔ `Herr`, `W` ➔ `Frau` |
| 🏠 **Straße trennen** | Extrahiert nur den Straßennamen | `Hauptstraße 12a` ➔ `Hauptstraße` |
| 🔢 **Hausnummer trennen** | Extrahiert nur die Hausnummer | `Hauptstraße 12a` ➔ `12a` |
| 🔗 **Spalten verknüpfen** | Fügt zwei Quellspalten mit Leerzeichen zusammen | `Musterstr.` + `4` ➔ `Musterstr. 4` |

---

## 📐 Eigene Schemata hinzufügen (`schemas.py`)

In der Datei `schemas.py` können beliebige weitere Zielstrukturen und Beschränkungen definiert werden:

```python
SCHEMAS = {
    "meine_tabelle": {
        "id": "VARCHAR(40)",
        "vorname": "VARCHAR(60)",
        "nachname": "VARCHAR(60)",
        "geburtsdatum": "DATE",
        "bemerkung": "TEXT"
    }
}
```

---

## 📄 Lizenz & Mitwirkung

Dieses Projekt steht unter der **MIT-Lizenz**. Beiträge, Issue-Meldungen und Feature-Wünsche sind herzlich willkommen!
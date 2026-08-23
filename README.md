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
* **KVNR Auto-Korrektur (`validate_kvnr`)**: Erkennt typische OCR-/Eingabefehler bei Krankenversichertennummern (z. B. Verwechslung von `0` und `O` am Anfang) und stellt gültige KVNRs automatisch wieder her, wenn die Korrektur am Ende eine gültige Prüfziffer enthält.
* **IK-Nummern-Validierung (`validate_ik`)**: Prüft Institutionskennzeichen nach der Prüfziffern-Logik der Gesetzlichen Krankenversicherung.
* **E-Mail-Validierung (`validate_email`)**: Identifiziert syntaktisch fehlerhafte E-Mail-Adressen.
* **Straße & Hausnummer trennen**: Extrahiert Straßenname oder Hausnummer zuverlässig – inklusive intelligenter Fallback-Logik für Straßen ohne Hausnummer (z. B. *"Auf den Hüllen"*).
* **UID-Generierung**: Erzeugt eindeutige, kompakte Base36-IDs basierend auf Zeitstempeln.
* **Datumsformatierung**: Konvertiert uneinheitliche Datumsformate (`DD.MM.YYYY`, `YYYY/MM/DD`, etc.) zuverlässig in das ISO-Format `YYYY-MM-DD`. Erlaubt zusätzliches Befüllen von leeren Feldern mit einem einstellbaren Fallbackwert.
* **PLZ-Bereinigung**: Entfernt Fließkomma-Reste (`.0`).
* **Geschlechts-Normalisierung**: Konvertiert Kürzel (`M`/`W`/`F`) in Anreden (`Herr`/`Frau`).
* **Zwei Spalten verknüpfen**: Verknüpft zwei Quellspalten mit Leerzeichen in einer Zielspalte. (z.B. "Straße" und "Hausnummer" => "Straße Hausnummer")
* **Sonderzeichen-Bereinigung**: Säubert unerwünschte Zeichen in Namen und Freitexten.

* ⚠️ **Zellgenaue VARCHAR-Längenprüfung**: Erkennt Überschreitungen von Datentyp-Begrenzungen im Zielschema und bietet einen Dialog zur Einzel- oder Massenbearbeitung.
* 🛡️ **Ungemappte Spalten sichern**: Speichert alle nicht zugewiesenen Quellspalten automatisch in einer separaten Restdatei (`REST_UNMAPPED_...csv`), damit keine Daten verloren gehen.<br>Erlaubt auch die Erstellung für Zusatzdatentabellen für manche Datenbanksysteme.
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

* Python **3.14** oder neuer
* Betriebssystem: Windows, macOS oder Linux

### Installation

#### 1. **Repository klonen oder Projektordner öffnen:**

```bash
git clone https://github.com/tgbox/pygrator.git
cd pygrator
```

#### 2. **Virtuelle Umgebung erstellen (optional, aber empfohlen):**

```bash
python -m venv .venv
# Unter Windows aktivieren:
.venv\Scripts\activate
# Unter macOS/Linux aktivieren:
source .venv/bin/activate
```

#### 3. **Erforderliche Abhängigkeiten installieren:**

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

Wähle aus dem Dropdown-Menü **„Zielschema“** die Zielstruktur der Datenbank aus (z. B. `patienten` oder `adressen`).<br>Du kannst in der Datei `schemas.py` auch eigene Definitionen hinzufügen.

### 3. Spalten-Zuordnung (Mapping)

Die App ordnet Quellspalten anhand Namensgleichheit und einiger weiterer vorab definierter Regeln automatisch zu. Du kannst die Dropdown-Menüs in der Spalte **„Quellspalte (CSV)“** manuell anpassen oder per Rechtsklick auf `-- Nicht zuordnen / Spezielle Regel --` stellen.

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

## 🛠️ Spalten-Zuordnungen, Auto-Fix-Muster & Transformationsregeln

### 🤖 1. Automatische Spalten-Zuweisungen (Auto-Mapping)

Beim Laden einer CSV-Quelldatei führt Pygrator einen automatischen Namensabgleich durch, um Quellspalten den vordefinierten Zielspalten des Zielschemas (z. B. `patienten` oder `adressen`) zuzuordnen:

| Zielspalte(n) im Schema | Erkannte Quellspalten-Namen (Case-Insensitive) | Zuordnungs-Typ / Bedeutung |
| :--- | :--- | :--- |
| **`name1`** | `titel` | Akademischer / Medizinischer Titel |
| **`name2`**, **`p_vname`** | `vorname` | Vorname des Patienten |
| **`name3`**, **`p_name`** | `nachname` | Nachname des Patienten |
| **`p_ort`**, **`ort`** | `ort`, `wohnort`, `stadt` | Wohnort / Stadt |
| **`p_plz`**, **`plz`** | `plz`, `postleitzahl` | Postleitzahl |
| **`p_birth`**, **`geburtsdatum`** | `geburtsdatum` | Geburtsdatum |
| **`p_anrede`**, **`anrede`** | `geschlecht` | Anrede / Geschlecht |
| **`telefonmobil`**, **`mobil`**, **`p_handy`** | `mobil`, `handy`, `mobile`, `telefonmobil` | Mobiltelefonnummer |
| **`telefon`**, **`p_tel`**, **`tel`** | `telefon`, `p_tel`, `tel`, `telefon1` | Festnetz-Telefonnummer |
| **`p_telge`** | `telefon2` | Geschäftliche Telefonnummer |
| **`p_street`**, **`p_hausnummer`** | `strasse`, `straße` | Straßenadresse / Hausnummer |
| **`p_ik`** | `kas_ik` | Krankenkassen-Institutionskennzeichen (IK) |
| **`p_vs`** | `status` | Versichertenstatus |
| **`p_vnr`** | `versichertennummer` | Krankenversichertennummer (KVNR) |
| **`p_nr`**, **`ext_id`** | `id`, `patient_id`, `patienten_id`, `pat_id`, `lanr` | Eindeutige ID-Spalte aus der Quelldatei |
| *Substrings (>3 Zeichen)* | Teilstrings aus Quell- & Zielspalten-Namen | Automatische Ähnlichkeitszuordnung |

---

### 2. Auto-Vervollständigungs- & Korrekturmuster (Auto-Fix)

Pygrator enthält intelligente Auto-Korrektur-Algorithmen, um fehlerhafte Eingaben, Tippfehler oder Ablesefehler aus Scans/OCR beim Datenimport automatisch zu reparieren:

#### ✉️ E-Mail-Adressen (`clean_email` / `try_to_fix_email`)

| Fehlerart / Musterschema | Beispiel Quelldaten | Automatisch korrigiertes Ergebnis | angewendete Korrekturregel |
| :--- | :--- | :--- | :--- |
| **Umlaute & Eszett** | `jörgen.müller@gmx.de` | `joergen.mueller@gmx.de` | Wandelt `ä`/`ö`/`ü`/`ß` kodierungssicher um (`ae`, `oe`, `ue`, `ss`). |
| **Tastaturfehler `Q`/`q` statt `@`** | `m.handelqt-online.de` | `m.handel@t-online.de` | Korrigiert `q`/`Q` (AltGr+Q Tippfehler) vor Domains zu `@`. |
| **T-Online Tastaturfehler** | `rudipT-online.de` | `rudip@t-online.de` | Ergänzt fehlendes `@` vor `T-online.de`. |
| **Fehlendes `t` bei T-Online** | `dehner@-online.de` | `dehner@t-online.de` | Repariert `@-online.de` zu `@t-online.de`. |
| **Fehlerhafter Punkt im Provider** | `max.lauren@t.-online.de` | `max.lauren@t-online.de` | Entfernt Punkte zwischen Provider-Bestandteilen (`t.-online` $\rightarrow$ `t-online`). |
| **Standard Domain-Tippfehler** | `max.mustermann@gamil.com` | `max.mustermann@gmail.com` | Repariert Schreibfehler (`gamil`, `gmeil`, `gmai` $\rightarrow$ `gmail.com`). |
| **Googlemail-Erhaltung** | `user@googlemail.com` | `user@googlemail.com` | Bleibt standardmäßig unverändert erhalten. Kann optional per Auto-Vervollständigungs-Option (`convert_googlemail`) zu `@gmail.com` vereinheitlicht werden. |
| **GMX / Web.de Tippfehler** | `hans.mueller@gmxde` | `hans.mueller@gmx.de` | Führt fehlende TLD-Punkte wieder ein (`gmxde` $\rightarrow$ `gmx.de`, `webde` $\rightarrow$ `web.de`). |
| **Fehlendes `@` bei Hauptdomains** | `usernamegmx.de` | `username@gmx.de` | Fügt `@` vor bekannten Provider-Domains (`gmx`, `web`, `gmail`, `hotmail`, `outlook`) ein. |
| **Formatierung & Klammern** | `(user@domain.de.)` | `user@domain.de` | Entfernt umschließende Satzzeichen/Klammern und bereinigt `@@` zu `@`. |
| **Mehrfach-E-Mails** | `a@b.de; c@d.de` | *Keine Auto-Korrektur* | Bleibt für die manuelle Prüfung im Validierungsdialog erhalten. |

#### 🆔 Krankenversichertennummer / KVNR (`clean_kvnr` / `try_to_fix_insurance_number`)

| Fehlerart / OCR-Muster | Beispiel Quelldaten | Korrigiertes Ergebnis | angewendete Korrekturregel |
| :--- | :--- | :--- | :--- |
| **Form `JO12345678`** | `JO12345678` | `J012345678` | Ersetzt `O` an 2. Stelle durch `0` (sofern Modulo-10-Prüfziffer valide). |
| **Form `0123456789`** | `0123456789` | `O123456789` | Ersetzt führende `0` durch den passenden Buchstaben `O`. |
| **Form `1200006986`** | `1200006986` | `I200006986` | Ersetzt führende `1` durch den Buchstaben `I`. |
| **Sonderzeichen `)`** | `)823672510` | `O823672510` | Korrigiert führende Klammer `)` zu `O`. |
| **Sonderzeichen `(`** | `(823672510` | `I823672510` | Korrigiert führende Klammer `(` zu `I`. |
| **Sonderzeichen `=` / `/`** | `=823672510` | `P823672510` | Korrigiert `=` zu `P` bzw. `/` zu `U`. |

#### 🏢 Institutionskennzeichen / IK (`validate_ik` / `validate_ik_number`)

| Eingabewert | Korrigiertes Ergebnis | Korrekturregel |
| :--- | :--- | :--- |
| `26012345.0` | `260123456` | Entfernt `.0` und prüft Stelle 9 auf Modulo-10 Prüfziffer. |

> **Hinweis zur automatischen Regel-Aktivierung:** Die Validierungsregeln `validate_ik`, `validate_kvnr` und `validate_email` werden beim Laden einer Datei nur dann automatisch aktiviert, wenn von Anfang an eine passende Quellspalte der jeweiligen Zielspalte zugeordnet wurde.

#### 🎓 Titel & Namen (`split_title` / `extract_title_and_clean_name`)

| Eingabewert | Extrahierter Titel | Bereinigter Name | Korrekturregel |
| :--- | :--- | :--- | :--- |
| `Prof. Dr. med. dent. Max Mustermann` | `Prof. Dr. med. dent.` | `Max Mustermann` | Trennt akademische & medizinische Titel ab. |

#### ⚥ Geschlecht & Anrede (`infer_gender` / `infer_salutation`)

| Vorname | Ermitteltes Geschlecht | Generierte Anrede | Korrekturregel |
| :--- | :--- | :--- | :--- |
| `Sebastian` | `männlich` | `Herr` | Gleicht den Vornamen ab und erzeugt die passende Anrede. |
| `Elena` | `weiblich` | `Frau` | Gleicht den Vornamen ab und erzeugt die passende Anrede. |

#### 📮 Postleitzahl (`clean_plz` / `format_plz`)

| Eingabewert | Korrigiertes Ergebnis | Korrekturregel |
| :--- | :--- | :--- |
| `08033.0` | `08033` | Entfernt Fließkomma-Reste (`.0`). |

#### 📅 Datum (`format_date` / `format_date_iso`)

| Eingabewert | Korrigiertes Ergebnis | Korrekturregel |
| :--- | :--- | :--- |
| `15.08.1985` | `1985-08-15` | Wandelt deutsche und internationale Datumsformate in den ISO-Standard `YYYY-MM-DD` um. |

---

### ⚙️ 3. Alle anwendbaren Transformations- & Validierungsregeln

Übersicht aller 17 in Pygrator konfigurierbaren Regeln:

| Technischer Schlüssel | Name in der GUI | Kategorie | Beschreibung & Funktionsweise |
| :--- | :--- | :--- | :--- |
| **`generate_uid`** | **UID generieren** | Generierung | Erzeugt eine eindeutige, kompakte Base36-ID für Primärschlüssel. |
| **`copy_target`** | **Kopieren aus** | Zuordnung | Kopiert den Wert direkt aus einer auswählbaren Quellspalte. |
| **`format_date`** | **Datum (YYYY-MM-DD)** | Konvertierung | Formatiert Datumsangaben in das Standard-ISO-Format `YYYY-MM-DD`. |
| **`default_value`** | **Standardwert** | Fallback | Ersetzt leere Zellen oder `NULL`-Werte durch einen definierten Ersatzwert. |
| **`static_value`** | **Festwert** | Konstante | Belegt alle Zeilen der Zielspalte mit einem statischen Text oder Wert. |
| **`clean_plz`** | **PLZ (5-stellig)** | Bereinigung | Säubert Fließkommazahlen (`.0`) und bringt PLZs auf genau 5 Ziffern. |
| **`gender`** | **Geschlecht->Anrede** | Mapping | Wandelt Geschlechtskürzel oder Vornamen in Anreden (`Herr`/`Frau`) um. |
| **`split_street`** | **Nur Straße** | Extraktion | Extrahiert nur den Straßennamen aus einem kombinierten Adressfeld. |
| **`split_number`** | **Nur Hausnummer** | Extraktion | Extrahiert nur die Hausnummer aus einem kombinierten Adressfeld. |
| **`merge_columns`** | **Spalten zusammenführen** | Transformation | Verknüpft zwei Quellspalten mit Leerzeichen in einer Zielspalte. |
| **`lookup_ik_provider`** | **Krankenkasse aus IK** | Stimmigkeit | Ermittelt den Krankenkassennamen anhand des Institutionskennzeichens (IK). |
| **`lookup_plz_by_city`** | **PLZ aus Ort ergänzen** | Stimmigkeit | Ermittelt und ergänzt die Postleitzahl basierend auf dem Ortsnamen. |
| **`lookup_city_by_plz`** | **Ort aus PLZ ergänzen** | Stimmigkeit | Ermittelt und ergänzt den Ortsnamen basierend auf der 5-stelligen PLZ. |
| **`validate_ik`** | **IK-Nummer prüfen** | Validierung | Validiert 9-stellige Institutionskennzeichen inkl. Prüfziffer (wird nur bei zugeordneter Quellspalte automatisch aktiviert). |
| **`validate_kvnr`** | **Versichertennr. prüfen** | Validierung | Korrigiert O/0-Ablesefehler und prüft KVNR-Format inkl. Modulo-10 (wird nur bei zugeordneter Quellspalte automatisch aktiviert). |
| **`validate_email`** | **E-Mail prüfen** | Validierung | Validiert Mail-Syntax und wendet umfassende Auto-Fix-Logik an. |
| **`auto_sequence_6`** | **Lineare Nummerierung (6-stellig)** | Generierung | Erzeugt eine fortlaufende 6-stellige Nummer (z. B. `000001`, `000002`). |

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

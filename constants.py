from typing import Tuple

RULE_NAMES = {
    "generate_uid": "UID generieren",
    "copy_target": "Kopieren aus",
    "format_date": "Datum (YYYY-MM-DD)",
    "default_value": "Standardwert",
    "static_value": "Festwert",
    "clean_plz": "PLZ (5-stellig)",
    "gender": "Geschlecht->Anrede",
    "split_street": "Nur Straße",
    "split_number": "Nur Hausnummer",
    "split_title": "Nur Titel (z. B. Dr. med.)",
    "split_name_without_title": "Name ohne Titel",
    "merge_columns": "Spalten zusammenführen",
    "lookup_ik_provider": "Krankenkasse aus IK",
    "lookup_plz_by_city": "PLZ aus Ort ergänzen",
    "lookup_city_by_plz": "Ort aus PLZ ergänzen",
    "validate_ik": "IK-Nummer prüfen",
    "validate_kvnr": "Versichertennr. prüfen",
    "validate_email": "E-Mail prüfen",
    "auto_sequence_6": "Lineare Nummerierung (6-stellig)"
}

RULE_DESCRIPTIONS = {
    "generate_uid": "Erzeugt eine eindeutige, 12-stellige alphanumerische Kennung (UID) für jeden Datensatz.",
    "copy_target": "Übernimmt den bereinigten Wert aus einer anderen bereits verarbeiteten Zielspalte.",
    "format_date": "Konvertiert verschiedene Datumsformate einheitlich in den ISO-Standard YYYY-MM-DD.",
    "default_value": "Befüllt leere Datenfelder mit einem vorgegebenen Standard-Fallbackwert.",
    "static_value": "Weist allen Datensätzen in dieser Zielspalte ausnahmslos denselben statischen Festwert zu.",
    "clean_plz": "Entfernt führende/nachfolgende Leerzeichen und '.0'-Suffixe bei PLZ-Werten. Füllt die Postleitzahl mit führenden Nullen auf 5 Stellen auf.",
    "gender": "Konvertiert verschiedenartige Geschlechts- oder Anrededaten (z. B. 'M', '1', 'männlich') in standardisierte Anreden ('Herr' / 'Frau').",
    "split_street": "Trennt Hausnummern und Adresszusätze ab, um ausschließlich den Straßennamen in das Zielfeld zu übernehmen.",
    "split_number": "Extrahiert die Hausnummer inklusive eventueller Zusätze aus einer kombinierten Adresszeile.",
    "split_title": "Extrahiert akademische & medizinische Titel (z. B. Dr. med., Prof.) aus dem Namensfeld.",
    "split_name_without_title": "Entfernt akademische Titel und übernimmt ausschließlich den Namen in das Zielfeld.",
    "merge_columns": "Führt Werte aus zwei separaten Quellspalten mit einem Leerzeichen als Trennzeichen in eine Zielspalte zusammen.",
    "lookup_ik_provider": "Bestimmt den Namen der Krankenkasse anhand der Institutionskennzeichen-Nummer (IK).",
    "lookup_plz_by_city": "Ermittelt die entsprechende Postleitzahl basierend auf dem angegebenen Ortsnamen aus der internen Datenbank.",
    "lookup_city_by_plz": "Sucht automatisch den passenden Ortsnamen anhand der vorhandenen Postleitzahl in der Datenbank.",
    "validate_ik": "Überprüft Institutionskennzeichen (IK) auf Korrektheit und 9-stellige Formatierung.",
    "validate_kvnr": "Prüft Krankenversichertennummern auf Korrektheit und behebt bekannte Formatfehler (z. B. Ersetzen des Buchstaben 'O' durch '0').",
    "validate_email": "Bereinigt E-Mail-Adressen von Typografie-/Tippfehlern sowie Leerzeichen und verifiziert das E-Mail-Format.",
    "auto_sequence_6": "Erzeugt eine fortlaufende 6-stellige Nummerierung (z. B. 000001, 000002) für alle Datensätze.",
    "split_title": "Trennt akademische Titel (z. B. Dr. med.) vom Vornamen/Nachnamen und ordnet sie dem Titelfeld zu.",
    "infer_gender": "Ermittelt automatisch das biologische Geschlecht anhand des Vornamens aus einer Datenbank.",
    "infer_salutation": "Leitet automatisch die passende Anrede (Herr/Frau) basierend auf dem Vornamen oder Geschlecht ab.",
    "clean_kvnr": "Korrigiert typische Eingabefehler in Krankenversichertennummern automatisch.",
    "clean_email": "Korrigiert fehlerhaft formatierte E-Mail-Adressen automatisch.",
    "varchar_limit": "Kürzt Werte, die das maximale Zeichenlimit des Zielfelds in der Ziel-Datenbank überschreiten.",
    "string_cleanup": "Bereinigt Steuerzeichen, doppelte Leerzeichen und unerwünschte Sonderzeichen aus Freitextfeldern."
}
APP_WIDTH = 1040
APP_HEIGHT = 880
FONT_TYPE = "Roboto"
LABEL_FONT_BOLD: tuple[str, int, str] = (FONT_TYPE, 11, "bold")
LABEL_FONT: tuple[str, int] = (FONT_TYPE, 11)
LARGER_LABEL_FONT_BOLD: tuple[str, int, str] = (FONT_TYPE, 14, "bold")
SMALL_LABEL_FONT: tuple[str, int] = (FONT_TYPE, 10)
SMALL_LABEL_FONT_BOLD: tuple[str, int, str] = (FONT_TYPE, 10, "bold")
BUTTON_FONT: tuple[str, int, str] = (FONT_TYPE, 12, "bold")
TITLE_FONT: tuple[str, int, str] = (FONT_TYPE, 18, "bold")
BOLD_FONT: tuple[str, str] = (FONT_TYPE, "bold")
OPTIONS_MENU_WIDTH = 160
MAX_CHAR_READ = 4096
RULE_BUTTON_WIDTH = 240
COL_ORANGE = "#CF8700"
COL_DARK_ORANGE = "#855600"
COL_LIGHT_GREEN = "#2FA572"
COL_GREEN = "#00B800"
COL_DARK_GREEN = "#1E7E34"
COL_DARKER_GREEN = "#145A24"
COL_LIGHT_RED = "#E57373"
COL_WHITE = "#FFFFFF"
COL_BLACK = "#000000"
COL_PURPLE = "#800080"
COL_GRAY_20 = "#333333"
COL_GRAY_30 = "#4D4D4D"
COL_GRAY_35 = "#595959"
COL_GRAY_40 = "#666666"
COL_GRAY_45 = "#737373"
COL_GRAY_70 = "#B3B3B3"
TRANSFORMATION_DIALOG_WIDTH = 580
TRANSFORMATION_DIALOG_HEIGHT = 640
VALUE_FIELD_WIDTH = 200
ROW_VALIDATION_DIALOG_WIDTH = 980
ROW_VALIDATION_DIALOG_HEIGHT = 730
BATCH_PROCESS_BUTTON_WIDTH = 150
REPLACEMENT_INPUT_WIDTH = 180
EXTRA_FIELDS_DIALOG_WIDTH = 800
EXTRA_FIELDS_DIALOG_HEIGHT = 600
BUTTON_HEIGHT = 35
DB_FIELD_NAMES_WIDTH = 190
DROPDOWN_WIDTH = 130
VALIDATION_DIALOG_WIDTH = 850
VALIDATION_DIALOG_HEIGHT = 550
INFO_LABEL_WIDTH = 300
MANUAL_CHANGE_FIELD_WIDTH = 140
RADIO_BUTTON_LABEL_WIDTH = 90
STRING_CLEANUP_DIALOG_WIDTH = 1120
STRING_CLEANUP_DIALOG_HEIGHT = 700
REPLACEMENT_WRAP_LENGTH = 700
BUTTON_WIDTH = 120
SMALL_HEADER_WIDTH = 70
LARGE_HEADER_WIDTH = 220
CHECKBOX_LABEL_WIDTH = 50
PROCESS_BUTTON_WIDTH = 200
APP_APPEARANCE_MODE = "system" # Can be one of "light", "dark", "system".
APP_COLOR_THEME = "blue"
CHECKBOX_WIDTH = 30
HEADER_LABEL_WIDTH = 90
PADDING_XXS = 3
PADDING_XS = 5
PADDING_S = 8
PADDING_M = 10
PADDING_L = 15
PADDING_XL = 20
PADDING_XXL = 25
PADDING_XXXL = 45
AUTO_COMPLETE_DIALOG_WIDTH = 470
AUTO_COMPLETE_DIALOG_HEIGHT = 400
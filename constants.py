from typing import Tuple, Dict, List, Set, Any

# =============================================================================
# Rule Names & Descriptions Metadata
# =============================================================================

RULE_NAMES: Dict[str, str] = {
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

RULE_DESCRIPTIONS: Dict[str, str] = {
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
    "infer_gender": "Ermittelt automatisch das biologische Geschlecht anhand des Vornamens aus einer Datenbank.",
    "infer_salutation": "Leitet automatisch die passende Anrede (Herr/Frau) basierend auf dem Vornamen oder Geschlecht ab.",
    "clean_kvnr": "Korrigiert typische Eingabefehler in Krankenversichertennummern automatisch.",
    "clean_email": "Korrigiert fehlerhaft formatierte E-Mail-Adressen automatisch.",
    "varchar_limit": "Kürzt Werte, die das maximale Zeichenlimit des Zielfelds in der Ziel-Datenbank überschreiten.",
    "string_cleanup": "Bereinigt Steuerzeichen, doppelte Leerzeichen und unerwünschte Sonderzeichen aus Freitextfeldern."
}

# =============================================================================
# Auto-Complete & Data Cleaning Definitions
# =============================================================================

# Bekannte akademische und medizinische Titel
AC_TITLES: List[str] = [
    "Prof. Dr. med. dent.", "Prof. Dr. med.", "PD Dr. med. dent.", "PD Dr. med.", 
    "Dr. med. dent.", "Dr. med.", "Dr. rer. nat.", "Prof. Dr.",
    "Dr.", "Prof.", "PD"
]

# Grundlegende Zuordnungstabelle für Vornamen -> Geschlecht
AC_GENDER_FIRSTNAMES: Dict[str, Set[str]] = {
    "m": {"hans", "peter", "christian", "thomas", "sebastian", "stefan", "alexander", "michael"},
    "w": {"sabine", "amira", "sarah", "elena", "maria", "lisa", "monika", "julia"}
}

# Ersetzungstabelle für deutsche Umlaute und Eszett in E-Mails
AC_EMAIL_UMLAUTE_MAP: Dict[str, str] = {
    '\u00e4': 'ae', '\u00f6': 'oe', '\u00fc': 'ue', '\u00df': 'ss',
    '\u00c4': 'Ae', '\u00d6': 'Oe', '\u00dc': 'Ue'
}

# Bekannte E-Mail-Domain-Tippfehler und deren Korrekturen
AC_EMAIL_DOMAIN_FIXES: Dict[str, str] = {
    '-online.de': 't-online.de',
    '-online': 't-online.de',
    '-onlin.de': 't-online.de',
    '-online.d': 't-online.de',
    't.-online.de': 't-online.de',
    't.-online': 't-online.de',
    't.online.de': 't-online.de',
    't.online': 't-online.de',
    't.-online.d': 't-online.de',
    't-online': 't-online.de',
    't-onlin.de': 't-online.de',
    't-online.d': 't-online.de',
    'tonline.de': 't-online.de',
    't-online-de': 't-online.de',
    't-onlinede': 't-online.de',
    'gamil.com': 'gmail.com',
    'gmaill.com': 'gmail.com',
    'gmei.com': 'gmail.com',
    'gmai.com': 'gmail.com',
    'gmail.de': 'gmail.com',
    'gmailcom': 'gmail.com',
    'gamilcom': 'gmail.com',
    'gmxde': 'gmx.de',
    'gmxnet': 'gmx.net',
    'gmx.d': 'gmx.de',
    'gmz.de': 'gmx.de',
    'gmz.net': 'gmx.net',
    'gmx-de': 'gmx.de',
    'gmx-net': 'gmx.net',
    'webde': 'web.de',
    'web.d': 'web.de',
    'webe.de': 'web.de',
    'wb.de': 'web.de',
    'web-de': 'web.de',
    'freenetde': 'freenet.de',
    'frenet.de': 'freenet.de',
    'freenet.d': 'freenet.de',
    'freenet-de': 'freenet.de',
    'hotmial.com': 'hotmail.com',
    'hotmai.com': 'hotmail.com',
    'hotmailde': 'hotmail.de',
    'hotmial.de': 'hotmail.de',
    'hotmailcom': 'hotmail.com',
    'hotmialcom': 'hotmail.com',
    'outlok.com': 'outlook.com',
    'outlok.de': 'outlook.de',
    'outlookde': 'outlook.de',
    'outlookcom': 'outlook.com',
    'yaho.de': 'yahoo.de',
    'yaho.com': 'yahoo.com',
    'yahoode': 'yahoo.de',
    'yahoocom': 'yahoo.com',
    'icould.com': 'icloud.com',
    'icloud.de': 'icloud.com',
    'icloudcom': 'icloud.com',
    '1&1.de': '1und1.de',
    '1und1de': '1und1.de',
    'vodafon.de': 'vodafone.de',
    'vodafonede': 'vodafone.de',
    'arcorde': 'arcor.de',
}

# Default Auto-Complete UI Einstellungen (CSVMappingApp)
DEFAULT_AUTOCOMPLETE_SETTINGS: Dict[str, bool] = {
    "infer_gender": False,
    "infer_salutation": False,
    "clean_kvnr": False,
    "clean_email": True,
    "convert_googlemail": False,
    "clean_umlaute": False,
}

# Default Auto-Complete UI Einstellungen (ImportApp)
DEFAULT_IMPORT_AUTOCOMPLETE_SETTINGS: Dict[str, bool] = {
    "infer_gender": True,
    "infer_salutation": True,
    "clean_kvnr": True,
    "clean_date_formats": True,
    "infer_insurance_name": True,
    "infer_city_name": True,
    "infer_plz": True,
    "validate_email": True,
    "clean_email": True,
    "convert_googlemail": False,
    "clean_umlaute": False,
}

# Optionen für das Auto-Complete Einstellungsfenster
AUTOCOMPLETE_OPTIONS_LIST: List[Tuple[str, str]] = [
    ("infer_gender", "⚥ Geschlecht anhand des Vornamens erraten"),
    ("infer_salutation", "✉️ Anrede (Herr/Frau) aus Geschlecht/Name abstatten"),
    ("clean_kvnr", "🆔 KVNR-Ablesefehler automatisch korrigieren ('O' -> '0', Modulo-10 Auto-Fix)"),
    ("clean_date_formats", "Datumsformat automatisch korrigieren"),
    ("infer_insurance_name", "Krankenkassenname automatisch ergänzen"),
    ("infer_city_name", "Ortsnamen aus PLZ ableiten"),
    ("infer_plz", "PLZ aus Ortsnamen ableiten"),
    ("validate_email", "E-Mail Adresse validieren"),
    ("clean_email", "📧 Fehlerhafte E-Mail-Adressen automatisch korrigieren"),
    ("convert_googlemail", "📧 @googlemail.com zu @gmail.com vereinheitlichen"),
    ("clean_umlaute", "🔤 Umlaute & Eszett in E-Mails ersetzen (ä->ae, ö->oe, ü->ue, ß->ss)")
]

# Zusatzfeld-Datentypen
EXTRA_FIELDS_PROPTYPES: List[str] = ["TXT", "NUM", "DATE", "BOOL"]

# =============================================================================
# GUI App & Dialog Titles
# =============================================================================

TITLE_MAIN_APP = "CSV Data Mapper & Schema Validator"
TITLE_ROW_VALIDATION_DIALOG = "⚠️ Individuelle Feldlängen-Konflikte lösen (Zellgenau)"
TITLE_EXTRA_FIELDS_DIALOG = "⚙️ Zusatzfelder für ungemappte Spalten definieren"
TITLE_VALIDATION_FIX_DIALOG = "⚠️ Validierungsfehler korrigieren"
TITLE_STRING_CLEANUP_DIALOG = "🔍 Vorschau: String-Bereinigung"
TITLE_AUTOCOMPLETE_SETTINGS_DIALOG = "⚙️ Einstellungen: Automatische Vervollständigung"
TITLE_TRANS_DIALOG = "Spezielle Regel & Transformation wählen"

# =============================================================================
# GUI Labels & Option Values
# =============================================================================

TXT_LOAD_CSV = "Quelldatei laden (CSV)"
TXT_AUTO_COMPLETE_SETTINGS = "⚙️ Auto-Vervollständigung"
LBL_TARGET_SCHEMA = "Zielschema:"
LBL_NO_FILE_SELECTED = "Keine Datei ausgewählt"
LBL_COLUMN_MAPPING_FRAME = "Spalten-Zuordnung & Schema-Limits"
CHK_FILL_NULL = "Unbelegte Felder mit 'NULL' auffüllen (statt leerem Text)"
CHK_CLEAN_STRINGS = "String-Werte bereinigen (Trim & Steuerzeichen entfernen)"
LBL_EXPORT_FORMAT = "Export-Format:"
LBL_ENCODING = "Encoding:"
CHK_AUDIT_EXPORT = "📋 Regelübersicht & Änderungskontroll-Protokoll generieren"
BTN_PROCESS_EXPORT = "Prüfen & Exportieren"
LBL_AUTOCOMPLETE_DIALOG_SUB = "Welche Regeln sollen beim Import angewendet werden?"

EXPORT_FORMAT_OPTIONS: List[str] = ["CSV (Semikolon ';')", "CSV (Komma ',')", "Excel (.xlsx)"]
EXPORT_ENCODING_OPTIONS: List[str] = ["utf-8-sig (Excel CSV)", "utf-8", "cp1252 (Windows)", "iso-8859-1"]
TXT_SPECIAL_RULE_OPTION = "-- Nicht zuordnen / Spezielle Regel --"

LBL_HEADER_TARGET_COL = "Zielspalte (Datentyp)"
LBL_HEADER_SOURCE_COL = "Quellspalte (CSV)"
LBL_HEADER_TRANSFORMATION = "Spezielle Transformation"
BTN_RULE_SELECT = "Regel hinzufügen..."
BTN_RULE_ACTIVE_PREFIX = "✓ "

# Buttons & Actions
TXT_BULK_TRUNCATE = "Alle automatisch kürzen"
TXT_BULK_IGNORE = "Alle unverändert lassen"
TXT_BULK_KEEP = "Alle beibehalten (Ignorieren)"
TXT_BULK_CLEAR = "Alle leeren (NULL)"
TXT_BULK_CLEAN = "✅ Alle bereinigen"
TXT_BULK_KEEP_CLEANUP = "❌ Alle beibehalten"

TXT_APPLY_EXPORT = "Entscheidungen anwenden & Exportieren"
TXT_APPLY_EXTRA_FIELDS = "Zusatzfelder übernehmen & Exportieren"
TXT_APPLY_VALIDATION_FIX = "Änderungen übernehmen & Exportieren"
TXT_APPLY_CONFIRM = "Änderungen übernehmen"
TXT_CANCEL = "Abbrechen"
TXT_SKIP = "Überspringen"
TXT_SAVE = "Übernehmen"
TXT_SAVE_RULE = "Speichern"
TXT_DELETE_RULE = "Regel löschen"

# Toast & Message Box Texts
MSG_ERR_NO_FILE_TITLE = "Fehler"
MSG_ERR_NO_FILE = "Keine Datei geladen!"
MSG_ERR_LOAD_EXCEL_TITLE = "Fehler beim Laden"
MSG_ERR_LOAD_FILE = "Konnte die Datei nicht lesen."

TOAST_EXPORT_SUCCESS_AUDIT = "Export erfolgreich abgeschlossen inkl. Regelübersicht & Änderungskontroll-Protokoll."
TOAST_EXPORT_SUCCESS_PATIENTEN = "Die Patientendaten sowie die Zusatzfelder-Tabellen wurden erfolgreich exportiert."
TOAST_EXPORT_SUCCESS_ADRESSEN = "Die Adressen wurden erfolgreich exportiert."

# Transformation Dialog RadioButton Labels & Field Labels
TXT_RULE_GENERATE_UID = "🔑 Neue UID generieren (Kompakt)"
TXT_RULE_COPY_TARGET = "🔗 Wert aus anderer Zielspalte übernehmen"
TXT_RULE_FORMAT_DATE = "📅 Datumsformat anpassen -> YYYY-MM-DD"
TXT_RULE_DEFAULT_VAL = "✨ Standardwert nur für LEERE Felder setzen"
TXT_RULE_STATIC_VAL = "📌 Statischen Festwert für ALLE Zeilen setzen"
TXT_RULE_LOOKUP_IK = "🏢 Krankenkassenname aus IK-Quellspalte ermitteln"
TXT_RULE_VALIDATE_IK = "✔️ IK-Nummer auf Gültigkeit prüfen (Prüfziffer)"
TXT_RULE_VALIDATE_KVNR = "✔️ Krankenversichertennummer (KVNR) auf Gültigkeit prüfen"
TXT_RULE_VALIDATE_EMAIL = "✔️ E-Mailadresse auf Gültigkeit prüfen"
TXT_RULE_CLEAN_PLZ = "📮 PLZ bereinigen (.0 entfernen & 5 Stellen)"
TXT_RULE_AUTO_SEQ6 = "🔢 Lineare Nummerierung (6-stellig, z. B. 000001)"
TXT_RULE_LOOKUP_PLZ = "📮 PLZ basierend auf Ortsname-Quellspalte ergänzen"
TXT_RULE_LOOKUP_CITY = "🏙️ Ort basierend auf PLZ-Quellspalte ergänzen"
TXT_RULE_GENDER = "👫 Geschlecht mappen (M->Herr, W->Frau)"
TXT_RULE_SPLIT_STREET = "🏠 Straße/(Hausnr.) trennen -> Nur Straßenname"
TXT_RULE_SPLIT_NUMBER = "🔢 (Straße)/Hausnr. trennen -> Nur Hausnummer"
TXT_RULE_SPLIT_TITLE = "🎓 Titel/Name trennen -> Nur Titel (z. B. Dr. med.)"
TXT_RULE_SPLIT_NAME_NO_TITLE = "🎓 Titel/Name trennen -> Name ohne Titel"
TXT_RULE_MERGE_COLUMNS = "🔗 Zwei Quellspalten zusammenführen (mit Leerzeichen)"

LBL_COPY_FROM = "Kopieren aus:"
LBL_DEFAULT_DATE_HINT = "Standardwert bei leeren Feldern (optional):"
CHK_LOG_AFFECTED_ROWS = "📋 Betroffene Quellzeilen in separater Liste/Tabelle erfassen"
LBL_REPLACEMENT_VAL = "Ersatzwert:"
LBL_VALUE = "Wert:"
LBL_IK_SOURCE_COL = "IK-Quellspalte:"
LBL_CITY_SOURCE_COL = "Ortsname-Quellspalte:"
LBL_PLZ_SOURCE_COL = "PLZ-Quellspalte:"
LBL_SECOND_SOURCE_COL = "Zweite Quellspalte:"

# =============================================================================
# Validation & Database Utilities Definitions
# =============================================================================

BASE36_ALPHABET: str = "0123456789abcdefghijklmnopqrstuvwxyz"
IK_CHECK_WEIGHTS: List[int] = [2, 1, 2, 1, 2, 1]
KVNR_CHECK_WEIGHTS: List[int] = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
NULL_STRING_VALUES: Set[str] = {"nan", "none", "null", "<na>", ""}

# =============================================================================
# GUI Styling & Layout Constants
# =============================================================================

APP_WIDTH = 1140
APP_HEIGHT = 880
FONT_TYPE = "Roboto"
LABEL_FONT_BOLD: Tuple[str, int, str] = (FONT_TYPE, 11, "bold")
LABEL_FONT: Tuple[str, int] = (FONT_TYPE, 11)
LARGER_LABEL_FONT_BOLD: Tuple[str, int, str] = (FONT_TYPE, 14, "bold")
SMALL_LABEL_FONT: Tuple[str, int] = (FONT_TYPE, 10)
SMALL_LABEL_FONT_BOLD: Tuple[str, int, str] = (FONT_TYPE, 10, "bold")
BUTTON_FONT: Tuple[str, int, str] = (FONT_TYPE, 12, "bold")
TITLE_FONT: Tuple[str, int, str] = (FONT_TYPE, 18, "bold")
BOLD_FONT: Tuple[str, str] = (FONT_TYPE, "bold")

OPTIONS_MENU_WIDTH = 160
MAX_CHAR_READ = 4096
RULE_BUTTON_WIDTH = 240

# =============================================================================
# GUI Functional & Semantic Color Palette (Light Mode, Dark Mode)
# =============================================================================

COLOR_TEXT_PRIMARY: Tuple[str, str] = ("#0F172A", "#FFFFFF")       # Primary text color
COLOR_TEXT_DARK: Tuple[str, str] = ("#0F172A", "#0F172A")          # Dark text color
COLOR_TEXT_MUTED: Tuple[str, str] = ("#334155", "#94A3B8")         # High contrast muted / hint text color (Slate 700 / 400)
COLOR_TEXT_DANGER: Tuple[str, str] = ("#DC2626", "#F87171")        # Danger / error text color
COLOR_TEXT_WARNING: Tuple[str, str] = ("#92400E", "#FCD34D")       # High contrast warning text color

COLOR_BTN_TEXT: Tuple[str, str] = ("#FFFFFF", "#FFFFFF")            # White text for dark action buttons
COLOR_BTN_SECONDARY_TEXT: Tuple[str, str] = ("#0F172A", "#FFFFFF")  # High contrast text for secondary buttons

COLOR_BTN_SUCCESS_BG: Tuple[str, str] = ("#046C4E", "#047857")     # WCAG compliant Success button background (Emerald 700)
COLOR_BTN_SUCCESS_HOVER: Tuple[str, str] = ("#03543F", "#065F46")  # Success button hover
COLOR_BTN_SUCCESS_ACTIVE: Tuple[str, str] = ("#014737", "#046C4E") # Active success button hover

COLOR_BTN_SECONDARY_BG: Tuple[str, str] = ("#E2E8F0", "#334155")   # Secondary button background (Slate 200 / 700)
COLOR_BTN_SECONDARY_HOVER: Tuple[str, str] = ("#CBD5E1", "#475569")# Secondary button hover

COLOR_BTN_NEUTRAL_BG: Tuple[str, str] = ("#F1F5F9", "#1E293B")     # Neutral action button background
COLOR_BTN_NEUTRAL_HOVER: Tuple[str, str] = ("#E2E8F0", "#334155")  # Neutral action button hover

COLOR_CONTAINER_BG_DARK: Tuple[str, str] = ("#F8FAFC", "#0F172A")  # Bar / header container background
COLOR_CARD_BG: Tuple[str, str] = ("#F1F5F9", "#1E293B")            # Card / frame background
COLOR_SEPARATOR: Tuple[str, str] = ("#CBD5E1", "#334155")          # Divider lines & frame borders

COLOR_TOAST_BG: Tuple[str, str] = ("#0F172A", "#1E293B")           # Floating Toast Card (Dark Slate)
COLOR_TOAST_BORDER: Tuple[str, str] = ("#059669", "#10B981")       # Subtle Emerald accent border
COLOR_TOAST_TEXT: Tuple[str, str] = ("#FFFFFF", "#FFFFFF")         # High contrast white text

COLOR_ACCENT_WARNING: Tuple[str, str] = ("#F59E0B", "#D97706")     # Warning badge / accent color
COLOR_ACCENT_SUCCESS: Tuple[str, str] = ("#047857", "#34D399")     # WCAG compliant success accent color

# Backward-compatibility aliases for legacy color names
COL_WHITE = COLOR_TEXT_PRIMARY
COL_BLACK = COLOR_TEXT_DARK
COL_GRAY_70 = COLOR_TEXT_MUTED
COL_LIGHT_RED = COLOR_TEXT_DANGER
COL_GREEN = COLOR_BTN_SUCCESS_BG
COL_DARK_GREEN = COLOR_BTN_SUCCESS_HOVER
COL_DARKER_GREEN = COLOR_BTN_SUCCESS_ACTIVE
COL_GRAY_30 = COLOR_BTN_SECONDARY_BG
COL_GRAY_40 = COLOR_BTN_SECONDARY_HOVER
COL_GRAY_35 = COLOR_BTN_NEUTRAL_BG
COL_GRAY_45 = COLOR_BTN_NEUTRAL_HOVER
COL_GRAY_20 = COLOR_CONTAINER_BG_DARK
COL_PURPLE = COLOR_TOAST_BG
COL_ORANGE = COLOR_ACCENT_WARNING
COL_DARK_ORANGE = COLOR_TEXT_WARNING
COL_LIGHT_GREEN = COLOR_ACCENT_SUCCESS

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
APP_APPEARANCE_MODE = "system"  # Can be one of "light", "dark", "system".
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
AUTO_COMPLETE_DIALOG_HEIGHT = 370
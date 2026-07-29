# type: ignore
import re
import time
import random
import string
import pandas as pd

def encode_base36(num: int) -> str:
    """Function to generate a base 36 string from an int."""
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    if num == 0:
        return "0"
    
    arr: list[str] = []
    while num > 0:
        num, rem = divmod(num, 36)
        arr.append(alphabet[rem])
    return "".join(reversed(arr))

def generate_id() -> str:
    """Function to generate a unique identifier for elements."""
    timestamp_ms = int(time.time() * 1000)
    part1 = encode_base36(timestamp_ms)
    
    base36_chars = string.digits + string.ascii_lowercase
    part2 = "".join(random.choices(base36_chars, k=5))
    
    return f"{part1}-{part2}".upper()

def parse_varchar_limit(datatype_str: str) -> int | None:
    """Extrahiert das Limit aus einem Typ-String wie 'VARCHAR(40)' -> 40. Bei 'TEXT' -> None."""
    match = re.search(r'VARCHAR\((\d+)\)', str(datatype_str), re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def format_date_iso(val) -> str:
    """Wandelt Datumsangaben (z.B. '15.08.1985', '1985/08/15', '15.8.85') sauber in 'YYYY-MM-DD' um."""
    if pd.isna(val):
        return ""
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['nan', 'null', 'none', '']:
        return ""

    # Falls bereits YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', val_str):
        return val_str

    try:
        # Versuch per Pandas to_datetime mit automatischer/deutscher Formaterkennung
        parsed_dt = pd.to_datetime(val_str, dayfirst=True, errors='coerce')
        if pd.notna(parsed_dt):
            return parsed_dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    return val_str

def sanitize_data_string(text, remove_special_chars: bool = True) -> str:
    """
    Bereinigt Strings von Steuerzeichen und unerwünschten Sonderzeichen.
    Behält Leerzeichen zwischen Wörtern garantiert bei!
    """
    if pd.isna(text) or text is None:
        return ""

    text_str = str(text)

    # 1. Steuerzeichen (\r, \n, \t) & geschützte Leerzeichen (\xa0) durch normale Leerzeichen ersetzen
    text_str = text_str.replace('\xa0', ' ').replace('\x00', '')
    text_str = re.sub(r'[\r\n\t]+', ' ', text_str)

    # 2. Sonderzeichen entfernen – \s (alle Leerzeichen) IST EXPLIZIT ERLAUBT
    if remove_special_chars:
        # Erlaubt: A-Z, a-z, 0-9, Umlaute, ß, Leerzeichen (\s), Bindestrich, Apostroph, Punkt, Komma
        pattern = r'[^a-zA-Z0-9äöüÄÖÜß\s\-\'.,()/]'
        text_str = re.sub(pattern, '', text_str)

    # 3. Mehrfache Leerzeichen ("  ") auf genau EIN Leerzeichen (" ") reduzieren & Ränder trimmen
    return re.sub(r'\s+', ' ', text_str).strip()

def validate_ik_number(ik: str) -> bool:
    """Prüft, ob die IK-Nummer genau aus 9 Ziffern besteht."""
    if not ik:
        return True
    return bool(re.match(r'^\d{9}$', ik.strip()))

def validate_insurance_number(vnr: str) -> bool:
    """Prüft, ob die Versichertennummer dem Format A123456789 (1 Buchstabe + 9 Ziffern) entspricht."""
    if not vnr:
        return True
    return bool(re.match(r'^[A-Z-a-z]\d{9}$', vnr.strip()))
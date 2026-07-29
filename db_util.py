# type: ignore
import re
import time
import random
import string
import pandas as pd

import email_validator as eval

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

def sanitize_data_string(val: str, remove_special_chars: bool = False) -> str:
    if not val or pd.isna(val):
        return ""
    
    val = str(val).strip()
    
    # 1. Steuerzeichen entfernen (Null-Bytes, Linefeeds etc.)
    val = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', val)
    
    # 2. Nur wirklich störende Zeichen entfernen
    if remove_special_chars:
        # Erlaubt: \w (Buchstaben/Zahlen/Akzente), Leerzeichen, '&', Apostrophe, 
        # Klammern, Slashes, Bindestriche, Plus, Punkte, @
        val = re.sub(r'[^\w\s&\'`’\(\)/@\._\+-]', '', val, flags=re.UNICODE)
        
    return val

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

def validate_email(email: str) -> bool:
    try:
        # Normalisiert die E-Mail (z.B. Kleinbuchstaben für Domains) und prüft Syntax
        valid = eval.validate_email(email, check_deliverability=False)
        
        # Returns True if condition is True: normalized_email = valid.normalized
        return True
    except eval.EmailNotValidError:
        return False
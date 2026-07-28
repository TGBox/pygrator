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

def center_window(window, width: int, height: int):
    # Aktualisiert die Geometrie-Informationen des Fensters
    window.update_idletasks()
    
    # Bildschirmmaße ermitteln
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Position berechnen
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    
    # Geometrie setzen: "Breite x Höhe + X-Offset + Y-Offset"
    window.geometry(f"{width}x{height}+{x}+{y}")
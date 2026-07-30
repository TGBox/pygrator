from collections.abc import Hashable
import re
import time
import random
import string
from typing import Any, Dict, List
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

def format_date_iso(val: str) -> str:
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
        _valid = eval.validate_email(email, check_deliverability=False)
        
        # Returns True if condition is True: normalized_email = valid.normalized
        return True
    except eval.EmailNotValidError:
        return False
    
def apply_rule_transform(val_str: str, rule_type: str, target_col: str) -> str:
    """
    Extrahiert Teilwerte vor der Längenprüfung.
    Trennt Straße und Hausnummer korrekt auf - auch bei Adressen ohne Hausnummer.
    """
    if not val_str:
        return ""

    rule_str = str(rule_type).lower() if rule_type else ""
    target_str = str(target_col).lower()

    # Ist es eine Hausnummern-Spalte?
    is_hnr = "hausnummer" in rule_str or "hnr" in rule_str or "hausnummer" in target_str or "hnr" in target_str
    # Ist es eine Straßen-Spalte?
    is_street = "strasse" in rule_str or "street" in rule_str or "strasse" in target_str or "street" in target_str

    if is_hnr:
        # Sucht gezielt nach einer Ziffer + optionalen Zusätzen am Ende (z.B. "19", "2a", "12-14")
        match = re.search(r'(\d+[\s]*[a-zA-Z\/-]*)$', val_str.strip())
        if match:
            return match.group(1).strip()
        # WICHTIG: Wenn KEINE Nummer enthalten ist (z.B. "Auf den Hüllen"), ist die Hausnummer LEER!
        return ""

    elif is_street:
        # Extrahiert alles VOR der ersten Hausnummern-Ziffer
        match = re.search(r'^(.*?)(?=\s+\d+)', val_str.strip())
        if match:
            return match.group(1).strip()
        # Falls keine Nummer da ist, gehört der GESAMTE String zur Straße!
        return val_str.strip()

    return val_str

def extract_flagged_records(
    df: pd.DataFrame, 
    mappings: List[Dict[str, str]]
) -> pd.DataFrame:
    """
    Identifiziert exakt die Datensätze mit echten Validierungs- oder Überlängenfehlern.
    """
    # 1. Any erlauben, da row.to_dict() und Zeilennummern verschiedene Typen enthalten
    flagged_rows: list[dict[Hashable, Any]] = []

    for idx, (_, row) in enumerate(df.iterrows()):
        row_flags: list[str] = []

        for m in mappings:
            source_col = m['source_col']
            target_col = m['target_col']
            limit = m['limit']
            tmp_rule_type = m.get('rule_type')
            if type(tmp_rule_type) == str: 
                rule_type = str(m.get('rule_type'))
            else:
                rule_type = "" #TODO: Check if this causes problems!
                

            if source_col not in df.columns:
                continue

            val = row[source_col]

            # Leere Felder / NaNs überspringen
            if pd.isna(val) or val is None:
                continue
            
            val_str = str(val).strip()
            if not val_str or val_str.lower() in ["nan", "none", "null", "<na>"]:
                continue

            # --- ZUERST: Extraktion durchführen! ---
            transformed_val = apply_rule_transform(val_str, rule_type, target_col)

            if not transformed_val:
                continue

            # --- 1. Sonderzeichen-Prüfung ---
            if rule_type not in ["validate_ik", "validate_kvnr"]:
                cleaned_str = sanitize_data_string(transformed_val, remove_special_chars=True)
                if cleaned_str != transformed_val:
                    row_flags.append(f"Sonderzeichen in '{source_col}' -> '{target_col}' ({transformed_val} -> {cleaned_str})")

            # --- 2. Überlänge auf dem EXTRAHIERTEN Wert prüfen ---
            if limit:
                if len(transformed_val) > int(limit):
                    row_flags.append(
                        f"Überlänge in '{target_col}' (aus '{source_col}'): "
                        f"'{transformed_val}' hat {len(transformed_val)} Zeichen (max. {limit})"
                    )

            # --- 3. Validierungen ---
            if rule_type == "validate_ik" or "ik" in target_col.lower():
                clean_ik_input = transformed_val.split('.')[0].zfill(9)
                if len(clean_ik_input) != 9 or not validate_ik_number(clean_ik_input):
                    row_flags.append(f"Ungültige IK in '{source_col}' ({val_str})")

            if rule_type == "validate_kvnr" or "kvnr" in target_col.lower() or "vnr" in target_col.lower():
                clean_kvnr_input = transformed_val.upper().strip()

                # 1. Versuche die Nummer zu reparieren (O <-> 0 Verwechslung)
                was_fixed, fixed_vnr = try_to_fix_insurance_number(clean_kvnr_input)
                
                # 2. Prüfe die (evtl. reparierte) Nummer mit deiner echten Validierung
                if validate_insurance_number(fixed_vnr):
                    if was_fixed:
                        # Optional: Als Hinweis flaggen, dass der Wert automatisch korrigiert werden kann
                        row_flags.append(f"KVNR in '{source_col}' korrigiert: ({clean_kvnr_input} -> {fixed_vnr})")
                else:
                    # Bleibt ungültig, selbst nach Reparaturversuch
                    row_flags.append(f"Ungültige KVNR in '{source_col}' ({val_str})")

        # Nur hinzufügen, wenn Abweichungen im transformierten Wert gefunden wurden
        if row_flags:
            row_dict = row.to_dict()
            # 2. idx explizit zu int konvertieren
            row_dict['__quell_zeile'] = idx + 2
            row_dict['__gefundene_fehler'] = " | ".join(row_flags)
            flagged_rows.append(row_dict)

    result_df = pd.DataFrame(flagged_rows)

    if not result_df.empty:
        cols = ['__quell_zeile', '__gefundene_fehler'] + [c for c in result_df.columns if c not in ['__quell_zeile', '__gefundene_fehler']]
        result_df = result_df[cols]

    return result_df

def try_to_fix_insurance_number(vnr: str) -> tuple[bool, str]:
    """Methode um fehlerhaft notierte Versicherungsnummern zu vervollständigen."""
    vnr = vnr.strip().upper()
    
    if len(vnr) == 10:
        # Case 1: Form wie JO12345678 => J012345678
        if vnr[0].isalpha() and vnr[1] == "O":
            return True, f"{vnr[0]}0{vnr[2:]}"
            
        # Case 2: Form wie 0123456789 => O123456789
        elif vnr.isnumeric() and vnr.startswith("0"):
            return True, f"O{vnr[1:]}"
        
        # Case 3: Form wie 1200006986 => I200006986
        elif vnr.isnumeric() and vnr.startswith("1"):
            return True, f"I{vnr[1:]}"
        
        # Case 4: Form wie )823672510 => O823672510
        elif vnr[1:].isnumeric() and vnr.startswith(")"):
            return True, f"O{vnr[1:]}"
        
        # Case 5: Form wie (823672510 => I823672510
        elif vnr[1:].isnumeric() and vnr.startswith("("):
            return True, f"I{vnr[1:]}"
        
        # Case 6: Form wie =823672510 => P823672510
        elif vnr[1:].isnumeric() and vnr.startswith("="):
            return True, f"P{vnr[1:]}"
        
        # Case 7: Form wie /823672510 => U823672510
        elif vnr[1:].isnumeric() and vnr.startswith("/"):
            return True, f"U{vnr[1:]}"
            
    return False, vnr
import re
from typing import Tuple

# Bekannte akademische und medizinische Titel
TITLES = [
    "Prof. Dr. med. dent.", "Prof. Dr. med.", "PD Dr. med.", 
    "Prof. Dr.", "Dr. med. dent.", "Dr. med.", "Dr. rer. nat.", 
    "Dr.", "Prof.", "PD"
]

# Grundlegende Zuordnungstabelle (erweiterbar)
GENDER_FIRSTNAMES = {
    "m": {"hans", "peter", "christian", "thomas", "sebastian", "stefan", "alexander", "michael"},
    "w": {"sabine", "amira", "sarah", "elena", "maria", "lisa", "monika", "julia"}
}

def extract_title_and_clean_name(full_name: str) -> Tuple[str, str]:
    """Trennt akademische Titel vom restlichen Namen ab."""
    cleaned_name = full_name.strip()
    extracted_title = ""
    
    for title in TITLES:
        # Prüfe, ob Name mit Titel beginnt (case-insensitive)
        pattern = re.compile(rf"^{re.escape(title)}\s+", re.IGNORECASE)
        if pattern.match(cleaned_name):
            extracted_title = title
            cleaned_name = pattern.sub("", cleaned_name).strip()
            break
            
    return extracted_title, cleaned_name


def infer_gender_and_salutation(first_name: str) -> Tuple[str, str]:
    """Ermittelt Geschlecht (m/w/d) und Anrede (Herr/Frau) basierend auf dem Vornamen."""
    name_key = first_name.strip().lower().split("-")[0] # Nimmt bei Doppelnamen den ersten Teil
    
    if name_key in GENDER_FIRSTNAMES["m"]:
        return "männlich", "Herr"
    elif name_key in GENDER_FIRSTNAMES["w"]:
        return "weiblich", "Frau"
    
    return "unbekannt", ""

def try_to_fix_insurance_number(vnr: str) -> tuple[bool, str]:
    """Methode um fehlerhaft notierte Versicherungsnummern zu vervollständigen."""
    from db_util import validate_insurance_number
    vnr = vnr.strip().upper()
    
    if len(vnr) == 10:
        # Case 1: Form wie JO12345678 => J012345678
        if vnr[0].isalpha() and vnr[1] == "O":
            tmp_fix = f"{vnr[0]}0{vnr[2:]}"
            if validate_insurance_number(tmp_fix):
                return True, tmp_fix
            
        # Case 2: Form wie 0123456789 => O123456789
        elif vnr.isnumeric() and vnr.startswith("0"):
            tmp_fix = f"O{vnr[1:]}"
            if validate_insurance_number(tmp_fix):
                return True, tmp_fix
        
        # Case 3: Form wie 1200006986 => I200006986
        elif vnr.isnumeric() and vnr.startswith("1"):
            tmp_fix = f"I{vnr[1:]}"
            if validate_insurance_number(tmp_fix):
                return True, tmp_fix
        
        # Case 4: Form wie )823672510 => O823672510
        elif vnr[1:].isnumeric() and vnr.startswith(")"):
            tmp_fix = f"O{vnr[1:]}"
            if validate_insurance_number(tmp_fix):
                return True, tmp_fix
        
        # Case 5: Form wie (823672510 => I823672510
        elif vnr[1:].isnumeric() and vnr.startswith("("):
            tmp_fix = f"I{vnr[1:]}"
            if validate_insurance_number(tmp_fix):
                return True, tmp_fix
        
        # Case 6: Form wie =823672510 => P823672510
        elif vnr[1:].isnumeric() and vnr.startswith("="):
            tmp_fix = f"P{vnr[1:]}"
            if validate_insurance_number(tmp_fix):
                return True, tmp_fix
        
        # Case 7: Form wie /823672510 => U823672510
        elif vnr[1:].isnumeric() and vnr.startswith("/"):
            tmp_fix = f"U{vnr[1:]}"
            if validate_insurance_number(tmp_fix):
                return True, tmp_fix
            
    return False, vnr


def try_to_fix_email(email: str) -> tuple[bool, str]:
    """Sucht nach häufigen Tippfehlern in E-Mail-Adressen und korrigiert diese."""
    from db_util import validate_email
    
    if not email:
        return False, ""

    orig = str(email).strip()
    cleaned = orig

    # 1. Leerzeichen entfernen (z. B. "max mueller@gmail.com" -> "maxmueller@gmail.com")
    cleaned = re.sub(r'\s+', '', cleaned)

    # 2. Tippfehler 'Q' anstelle von '@' korrigieren (z. B. mmQt-online.de -> mm@t-online.de)
    if '@' not in cleaned and 'Q' in cleaned:
        cleaned = re.sub(r'Q(?=[a-zA-Z0-9.-]+\.[a-zA-Z]{1,})', '@', cleaned)
        if '@' not in cleaned:
            cleaned = cleaned.replace('Q', '@', 1)

    if '@' not in cleaned:
        return False, orig

    parts = cleaned.split('@', 1)
    local_part = parts[0]
    domain_part = parts[1]

    # 3. Punkte unmittelbar vor oder nach dem '@' entfernen
    local_part = local_part.rstrip('.')
    domain_part = domain_part.lstrip('.')

    # 4. Doppelte/mehrfache Punkte in Domain bereinigen (z. B. mm@t-online..de -> mm@t-online.de)
    domain_part = re.sub(r'\.+', '.', domain_part)

    # 5. Falsche Trennzeichen (Komma, Semikolon, Doppelpunkt) vor TLD korrigieren
    domain_part = re.sub(r'[,;:]', '.', domain_part)
    domain_part = re.sub(r'\.+', '.', domain_part)

    domain_lower = domain_part.lower()

    # 6. Bekannte T-Online Muster & Tippfehler korrigieren
    if domain_lower in ['t-online', 't-onlin.de', 't-online.d', 'tonline.de', 't.online.de', 't.online'] or \
       re.match(r'^(t[-.]?online|tonline)(\.(de|d))?$', domain_lower):
        domain_part = 't-online.de'
    else:
        # 7. Fehlenden Punkt vor gängigen TLDs ergänzen (z. B. mm@gmxde -> mm@gmx.de)
        if '.' not in domain_part:
            match = re.match(r'^([a-zA-Z0-9-]+)(de|com|net|org|at|ch)$', domain_part, re.IGNORECASE)
            if match:
                domain_part = f"{match.group(1)}.{match.group(2)}"

    cleaned_email = f"{local_part}@{domain_part}"

    if cleaned_email != orig and validate_email(cleaned_email):
        return True, cleaned_email

    return False, orig
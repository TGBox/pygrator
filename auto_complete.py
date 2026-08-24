from typing import Any, Tuple
import re
import unicodedata
from constants import (
    AC_TITLES,
    AC_GENDER_FIRSTNAMES,
    AC_EMAIL_UMLAUTE_MAP,
    AC_EMAIL_DOMAIN_FIXES,
    NULL_STRING_VALUES,
)


def extract_title_and_clean_name(full_name: Any) -> Tuple[str, str]:
    """Trennt akademische Titel vom restlichen Namen ab."""
    if full_name is None:
        return "", ""
    name_str = str(full_name).strip()
    if not name_str or name_str.lower() in NULL_STRING_VALUES:
        return "", ""
    cleaned_name = name_str
    extracted_title = ""
    
    for title in AC_TITLES:
        # Prüfe, ob Name mit Titel beginnt (case-insensitive)
        pattern = re.compile(rf"^{re.escape(title)}\s+", re.IGNORECASE)
        if pattern.match(cleaned_name):
            extracted_title = title
            cleaned_name = pattern.sub("", cleaned_name).strip()
            break
            
    return extracted_title, cleaned_name


def infer_gender_and_salutation(first_name: Any) -> Tuple[str, str]:
    """Ermittelt Geschlecht (m/w/d) und Anrede (Herr/Frau) basierend auf dem Vornamen."""
    if not first_name:
        return "unbekannt", ""
    fn_str = str(first_name).strip()
    if not fn_str or fn_str.lower() in NULL_STRING_VALUES:
        return "unbekannt", ""
    name_key = fn_str.lower().split("-")[0] # Nimmt bei Doppelnamen den ersten Teil
    
    if name_key in AC_GENDER_FIRSTNAMES["m"]:
        return "männlich", "Herr"
    elif name_key in AC_GENDER_FIRSTNAMES["w"]:
        return "weiblich", "Frau"
    
    return "unbekannt", ""


def try_to_fix_insurance_number(vnr: Any) -> tuple[bool, str]:
    """Methode um fehlerhaft notierte Versicherungsnummern zu vervollständigen."""
    from db_util import validate_insurance_number
    if not vnr:
        return False, ""
    vnr_str = str(vnr).strip().upper()
    if not vnr_str or vnr_str.lower() in NULL_STRING_VALUES:
        return False, ""
    vnr = vnr_str
    
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


def try_to_fix_email(email: Any, convert_googlemail: bool = False, clean_umlaute: bool = False) -> tuple[bool, str]:
    """Sucht nach häufigen Tippfehlern in E-Mail-Adressen und korrigiert diese."""
    from db_util import validate_email
    
    if not email:
        return False, ""

    orig = str(email).strip()
    if not orig or orig.lower() in NULL_STRING_VALUES:
        return False, ""
    
    # 0. Vorab-Prüfung auf Mehrfach-Adressen (z. B. "a@b.de; c@d.de" oder "a@b.de, c@d.de")
    if re.search(r'@[^\s,;:]+[\s,;:]+.*@', orig):
        return False, orig

    cleaned = unicodedata.normalize('NFC', orig)

    # 1. Führende und nachfolgende Satzzeichen / Klammern entfernen
    cleaned = cleaned.strip(" .,;:!?<>(){}[]\"'")

    # 2. Deutsche Umlaute und Eszett optional ersetzen
    if clean_umlaute:
        for char, repl in AC_EMAIL_UMLAUTE_MAP.items():
            cleaned = cleaned.replace(char, repl)

    # 3. Leerzeichen entfernen
    cleaned = re.sub(r'\s+', '', cleaned)

    # 4. (at) / [at] / (AT) / [AT] durch '@' ersetzen
    cleaned = re.sub(r'(?i)[\(\[\{]at[\)\]\}]', '@', cleaned)

    # 5. Tippfehler 'Q' / 'q' anstelle von '@' korrigieren
    if '@' not in cleaned:
        cleaned = re.sub(r'(?i)[qQ](?=[-.]?(?:online|tonline)|\.[a-zA-Z0-9.-]+\.[a-zA-Z]{1,})', '@', cleaned)
        if '@' not in cleaned and 'Q' in cleaned:
            cleaned = cleaned.replace('Q', '@', 1)

    # 6. Fehlendes '@' vor bekannte Hauptdomains korrigieren
    if '@' not in cleaned:
        m_domain = re.search(r'(?i)^(.*?)(?<!@)((?:t[-.]?online|[-.]online)(?:\.de|\.d)?|gmx\.(?:de|net)|web\.de|gmail\.com|hotmail\.(?:com|de)|outlook\.(?:com|de)|freenet\.de|yahoo\.(?:de|com)|icloud\.com|1und1\.de)$', cleaned)
        if m_domain and m_domain.group(1).strip(' .-_'):
            local = m_domain.group(1).rstrip(' .-_')
            dom = m_domain.group(2).lower()
            if re.match(r'^(t[-.]?online|[-.]online)(\.(de|d))?$', dom):
                dom = 't-online.de'
            cleaned = f"{local}@{dom}"

    # 9. Mehrfache '@' bereinigen
    cleaned = re.sub(r'@+', '@', cleaned)

    if '@' not in cleaned:
        return False, orig

    parts = cleaned.split('@', 1)
    local_part = parts[0]
    domain_part = parts[1]

    if '@' in domain_part:
        return False, orig

    # 10. Punkte/Satzzeichen unmittelbar vor oder nach dem '@' entfernen
    local_part = local_part.strip(' .,;:')
    domain_part = domain_part.strip(' .,;:')

    # 11. Mehrfache Punkte in Domain bereinigen
    domain_part = re.sub(r'\.+', '.', domain_part)

    # 12. Falsche Trennzeichen in Domain korrigieren
    domain_part = re.sub(r'[,;:]', '.', domain_part)
    domain_part = re.sub(r'\.+', '.', domain_part)

    domain_lower = domain_part.lower()

    # 13. Bekannte Domain-Tippfehler korrigieren
    domain_fixes = AC_EMAIL_DOMAIN_FIXES.copy()

    if convert_googlemail:
        domain_fixes['googlemail.com'] = 'gmail.com'
        domain_fixes['googlemail.de'] = 'gmail.com'

    if domain_lower in domain_fixes:
        domain_part = domain_fixes[domain_lower]
    else:
        # 14. Fehlenden Punkt vor gängigen TLDs ergänzen
        if '.' not in domain_part:
            match = re.match(r'^([a-zA-Z0-9-]+)(de|com|net|org|at|ch)$', domain_part, re.IGNORECASE)
            if match:
                domain_part = f"{match.group(1)}.{match.group(2)}"

    cleaned_email = f"{local_part}@{domain_part}"

    if cleaned_email != orig and validate_email(cleaned_email):
        return True, cleaned_email

    return False, orig


def try_to_fix_salutation(salutation: Any) -> tuple[bool, str]:
    """Normalisiert uneinheitliche oder abgekürzte Anreden (z. B. 'Fr', 'Fräulein' -> 'Frau', 'Hr', 'Herrn' -> 'Herr', 'D', 'Div' -> 'Divers')."""
    if not salutation:
        return False, ""
    s_str = str(salutation).strip()
    if not s_str or s_str.lower() in NULL_STRING_VALUES:
        return False, ""

    s_lower = s_str.lower().rstrip(".")

    female_variants = {"fr", "f", "fräulein", "fraulein", "frl", "frau", "weiblich", "w"}
    male_variants = {"hr", "h", "herrn", "herr", "männlich", "maennlich", "m"}
    diverse_variants = {"d", "di", "div", "divers", "diverses", "x", "d/x"}

    if s_lower in female_variants:
        normalized = "Frau"
    elif s_lower in male_variants:
        normalized = "Herr"
    elif s_lower in diverse_variants:
        normalized = "Divers"
    else:
        return False, s_str

    if s_str != normalized:
        return True, normalized
    return False, s_str


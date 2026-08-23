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
def try_to_fix_email(email: str, convert_googlemail: bool = False) -> tuple[bool, str]:
    """Sucht nach häufigen Tippfehlern in E-Mail-Adressen und korrigiert diese."""
    from db_util import validate_email
    
    if not email:
        return False, ""

    orig = str(email).strip()
    
    # 0. Vorab-Prüfung auf Mehrfach-Adressen (z. B. "a@b.de; c@d.de" oder "a@b.de, c@d.de")
    # Falls mehr als eine vollwertige E-Mail enthalten ist, nicht automatisch verändern
    if re.search(r'@[^\s,;:]+[\s,;:]+.*@', orig):
        return False, orig

    import unicodedata
    cleaned = unicodedata.normalize('NFC', orig)

    # 1. Führende und nachfolgende Satzzeichen / Klammern entfernen (z. B. "user@domain.de.")
    cleaned = cleaned.strip(" .,;:!?<>(){}[]\"'")

    # 2. Deutsche Umlaute und Eszett ersetzen (Unicode-Escapes für Kodierungssicherheit)
    umlaute_map = {
        '\u00e4': 'ae', '\u00f6': 'oe', '\u00fc': 'ue', '\u00df': 'ss',
        '\u00c4': 'Ae', '\u00d6': 'Oe', '\u00dc': 'Ue'
    }
    for char, repl in umlaute_map.items():
        cleaned = cleaned.replace(char, repl)

    # 3. Leerzeichen entfernen (z. B. "max mueller @ gmail.com" -> "maxmueller@gmail.com")
    cleaned = re.sub(r'\s+', '', cleaned)

    # 4. (at) / [at] / (AT) / [AT] durch '@' ersetzen
    cleaned = re.sub(r'(?i)[\(\[\{]at[\)\]\}]', '@', cleaned)

    # 5. Tippfehler 'Q' / 'q' anstelle von '@' korrigieren (z. B. "m.haendgenq-online.de" -> "m.haendgen@-online.de", "mmQt-online.de" -> "mm@t-online.de")
    if '@' not in cleaned:
        cleaned = re.sub(r'(?i)[qQ](?=[-.]?(?:online|tonline)|\.[a-zA-Z0-9.-]+\.[a-zA-Z]{1,})', '@', cleaned)
        if '@' not in cleaned and 'Q' in cleaned:
            cleaned = cleaned.replace('Q', '@', 1)

    # 6. Fehlendes '@' vor 't-online.de' oder anderen bekannten Hauptdomains korrigieren (z. B. "renatepietteT-online.de" -> "renatepiette@t-online.de")
    if '@' not in cleaned:
        m_domain = re.search(r'(?i)^(.*?)(?<!@)((?:t[-.]?online|[-.]online)(?:\.de|\.d)?|gmx\.(?:de|net)|web\.de|gmail\.com|hotmail\.(?:com|de)|outlook\.(?:com|de)|freenet\.de|yahoo\.(?:de|com)|icloud\.com|1und1\.de)$', cleaned)
        if m_domain and m_domain.group(1).strip(' .-_'):
            local = m_domain.group(1).rstrip(' .-_')
            dom = m_domain.group(2).lower()
            if re.match(r'^(t[-.]?online|[-.]online)(\.(de|d))?$', dom):
                dom = 't-online.de'
            cleaned = f"{local}@{dom}"

    # 9. Mehrfache '@' bereinigen (z. B. "user@@gmail.com" -> "user@gmail.com")
    cleaned = re.sub(r'@+', '@', cleaned)

    if '@' not in cleaned:
        return False, orig

    parts = cleaned.split('@', 1)
    local_part = parts[0]
    domain_part = parts[1]

    # Falls domain_part noch ein '@' enthält, nicht automatisch anfassen
    if '@' in domain_part:
        return False, orig

    # 10. Punkte/Satzzeichen unmittelbar vor oder nach dem '@' entfernen
    local_part = local_part.strip(' .,;:')
    domain_part = domain_part.strip(' .,;:')

    # 11. Mehrfache Punkte in Domain bereinigen (z. B. mm@t-online..de -> mm@t-online.de)
    domain_part = re.sub(r'\.+', '.', domain_part)

    # 12. Falsche Trennzeichen (Komma, Semikolon, Doppelpunkt) in Domain korrigieren
    domain_part = re.sub(r'[,;:]', '.', domain_part)
    domain_part = re.sub(r'\.+', '.', domain_part)

    domain_lower = domain_part.lower()

    # 13. Bekannte Domain-Tippfehler korrigieren
    domain_fixes: dict[str, str] = {
        # T-Online spezifische Muster
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
        # Gmail
        'gamil.com': 'gmail.com',
        'gmaill.com': 'gmail.com',
        'gmei.com': 'gmail.com',
        'gmai.com': 'gmail.com',
        'gmail.de': 'gmail.com',
        'gmailcom': 'gmail.com',
        'gamilcom': 'gmail.com',
        # GMX
        'gmxde': 'gmx.de',
        'gmxnet': 'gmx.net',
        'gmx.d': 'gmx.de',
        'gmz.de': 'gmx.de',
        'gmz.net': 'gmx.net',
        'gmx-de': 'gmx.de',
        'gmx-net': 'gmx.net',
        # Web.de
        'webde': 'web.de',
        'web.d': 'web.de',
        'webe.de': 'web.de',
        'wb.de': 'web.de',
        'web-de': 'web.de',
        # Freenet
        'freenetde': 'freenet.de',
        'frenet.de': 'freenet.de',
        'freenet.d': 'freenet.de',
        'freenet-de': 'freenet.de',
        # Hotmail
        'hotmial.com': 'hotmail.com',
        'hotmai.com': 'hotmail.com',
        'hotmailde': 'hotmail.de',
        'hotmial.de': 'hotmail.de',
        'hotmailcom': 'hotmail.com',
        'hotmialcom': 'hotmail.com',
        # Outlook
        'outlok.com': 'outlook.com',
        'outlok.de': 'outlook.de',
        'outlookde': 'outlook.de',
        'outlookcom': 'outlook.com',
        # Yahoo
        'yaho.de': 'yahoo.de',
        'yaho.com': 'yahoo.com',
        'yahoode': 'yahoo.de',
        'yahoocom': 'yahoo.com',
        # iCloud
        'icould.com': 'icloud.com',
        'icloud.de': 'icloud.com',
        'icloudcom': 'icloud.com',
        # 1&1
        '1&1.de': '1und1.de',
        '1und1de': '1und1.de',
        # Vodafone / Arcor
        'vodafon.de': 'vodafone.de',
        'vodafonede': 'vodafone.de',
        'arcorde': 'arcor.de',
    }

    if convert_googlemail:
        domain_fixes['googlemail.com'] = 'gmail.com'
        domain_fixes['googlemail.de'] = 'gmail.com'

    if domain_lower in domain_fixes:
        domain_part = domain_fixes[domain_lower]
    else:
        # 14. Fehlenden Punkt vor gängigen TLDs ergänzen (z. B. mm@gmxde -> mm@gmx.de)
        if '.' not in domain_part:
            match = re.match(r'^([a-zA-Z0-9-]+)(de|com|net|org|at|ch)$', domain_part, re.IGNORECASE)
            if match:
                domain_part = f"{match.group(1)}.{match.group(2)}"

    cleaned_email = f"{local_part}@{domain_part}"

    if cleaned_email != orig and validate_email(cleaned_email):
        return True, cleaned_email

    return False, orig
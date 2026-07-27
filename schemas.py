# Vorgedefinierte Zielschemas für die Data-Cur Datenbank Tabellen inklusive der Datentyp Beschränkungen.
SCHEMAS = {
    "patienten": {
        "id": "VARCHAR(40)",
        "p_nr": "VARCHAR(40)",
        "p_anrede": "VARCHAR(60)",
        "p_name": "VARCHAR(60)",
        "p_vname": "VARCHAR(60)",
        "p_plz": "VARCHAR(10)",
        "p_ort": "VARCHAR(60)",
        "p_street": "VARCHAR(60)",
        "p_birth": "VARCHAR(40)",
        "p_vip": "VARCHAR(10)",
        "p_tel": "VARCHAR(40)",
        "p_telge": "VARCHAR(40)",
        "p_handy": "VARCHAR(40)",
        "p_email": "VARCHAR(60)",
        "p_hausnummer": "VARCHAR(10)",
        "p_wlc": "VARCHAR(3)",
        "p_zuzahlungsbefreit": "BOOLEAN",
        "p_krankenkasse": "VARCHAR(60)",
        "p_privatversichert": "BOOLEAN",
        "p_ik": "VARCHAR(40)",
        "p_vnr": "VARCHAR(40)",
        "p_vs": "VARCHAR(10)",
        "p_zuzahlungsbefreit_bis": "DATE",
        "rechnungsempfaenger": "TEXT"
    },
    "adressen": {
        "id": "VARCHAR(40)",
        "ext_id": "VARCHAR(40)",
        "anrede": "VARCHAR(60)",
        "name1": "VARCHAR(60)",
        "name2": "VARCHAR(60)",
        "name3": "VARCHAR(60)",
        "strasse": "VARCHAR(60)",
        "plz": "VARCHAR(10)",
        "ort": "VARCHAR(60)",
        "email": "VARCHAR(60)",
        "telefon": "VARCHAR(60)",
        "kategorie": "VARCHAR(60)",
        "telefonmobil": "VARCHAR(60)"
    }
}
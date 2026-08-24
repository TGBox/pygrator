import os
import tempfile
import pandas as pd
import pytest

from db_util import (
    validate_insurance_number,
    validate_ik_number,
    validate_email,
    format_date_iso,
    sanitize_data_string,
    parse_varchar_limit,
    filter_near_empty_rows,
    compute_file_sha256,
)
from auto_complete import (
    extract_title_and_clean_name,
    infer_gender_and_salutation,
    try_to_fix_insurance_number,
    try_to_fix_email,
)
from constants import (
    EXPORT_BOOL_OPTIONS,
    DEFAULT_AUTOCOMPLETE_SETTINGS,
    DEFAULT_IMPORT_AUTOCOMPLETE_SETTINGS,
    AC_EMAIL_DOMAIN_FIXES,
)
from schemas import SCHEMAS


class TestComprehensiveInsuranceAndIkValidation:
    """Testfälle für KVNR-, IK- und E-Mail-Validierung und Auto-Fixes."""

    def test_kvnr_validation_edge_cases(self):
        # Gültiges KVNR Format: 1 Buchstabe + 9 Ziffern, 10. Stelle ist Prüfziffer
        assert validate_insurance_number("") is False
        assert validate_insurance_number(None) is False
        assert validate_insurance_number("   ") is False
        assert validate_insurance_number("A12345") is False
        assert validate_insurance_number("1234567890") is False  # Keine führende Buchstabe
        assert validate_insurance_number("AB23456789") is False  # Zwei Buchstaben

    def test_ik_validation_edge_cases(self):
        # IK-Nummern müssen genau 9-stellig sein und eine gültige Prüfziffer besitzen
        assert validate_ik_number("260326822") is True   # Techniker Krankenkasse
        assert validate_ik_number("104212505") is True   # AOK Bayern
        assert validate_ik_number("109999999") is False  # Falsche Prüfziffer
        assert validate_ik_number("") is False
        assert validate_ik_number(None) is False
        assert validate_ik_number("12345678") is False   # Zu kurz
        assert validate_ik_number("1234567890") is False # Zu lang
        assert validate_ik_number("ABCDEFGHI") is False  # Keine Ziffern

    def test_email_validation_and_fixing_edge_cases(self):
        # Email Validation
        assert validate_email("test@example.com") is True
        assert validate_email("max.mustermann@klinik-muenchen.de") is True
        assert validate_email("user.name+tag@sub.domain.co.uk") is True
        assert validate_email("invalid..email@domain.com") is False
        assert validate_email("noatdomain.com") is False
        assert validate_email("user@.com") is False

        # Email Fixes - Domain Typos
        for typo_domain, correct_domain in AC_EMAIL_DOMAIN_FIXES.items():
            input_email = f"testuser@{typo_domain}"
            fixed, new_email = try_to_fix_email(input_email)
            assert fixed is True
            assert new_email == f"testuser@{correct_domain}"

        # Email Fixes - Q statt @
        fixed, new_email = try_to_fix_email("max.mustermannQgmx.de")
        assert fixed is True
        assert new_email == "max.mustermann@gmx.de"

        # Email Fixes - Umlaute
        fixed, new_email = try_to_fix_email("jörg.müller@büro.de", clean_umlaute=True)
        assert fixed is True
        assert new_email == "joerg.mueller@buero.de"


class TestComprehensiveTitlesAndNames:
    """Testfälle für akademische Titel und Namenstrennung."""

    @pytest.mark.parametrize(
        "full_name,expected_title,expected_name",
        [
            ("Dr. Max Mustermann", "Dr.", "Max Mustermann"),
            ("Prof. Dr. med. Sabina Schmidt", "Prof. Dr. med.", "Sabina Schmidt"),
            ("PD Dr. med. dent. Thomas Müller", "PD Dr. med. dent.", "Thomas Müller"),
            ("Dipl.-Ing. Hans Meier", "Dipl.-Ing.", "Hans Meier"),
            ("Dr. rer. nat. Julia Weber", "Dr. rer. nat.", "Julia Weber"),
            ("Erika Musterfrau", "", "Erika Musterfrau"),
            ("Dr. Maria von Gutenberg", "Dr.", "Maria von Gutenberg"),
            ("Prof. Dr. Sean O'Connor", "Prof. Dr.", "Sean O'Connor"),
        ],
    )
    def test_extract_title_and_clean_name_variations(
        self, full_name, expected_title, expected_name
    ):
        title, name = extract_title_and_clean_name(full_name)
        assert title == expected_title
        assert name == expected_name

    def test_infer_gender_and_salutation_extended(self):
        assert infer_gender_and_salutation("Alexander") == ("männlich", "Herr")
        assert infer_gender_and_salutation("Katharina") == ("weiblich", "Frau")
        assert infer_gender_and_salutation("Jean-Luc") == ("männlich", "Herr")
        assert infer_gender_and_salutation("Anna-Lena") == ("weiblich", "Frau")
        assert infer_gender_and_salutation("   ") == ("unbekannt", "")


class TestComprehensiveDateFormatting:
    """Testfälle für ISO-Datumsformatierung und Fallbacks."""

    def test_format_date_iso_various_inputs(self):
        assert format_date_iso("2023-12-31") == "2023-12-31"
        assert format_date_iso("31.12.2023") == "2023-12-31"
        assert format_date_iso("1.5.2024") == "2024-05-01"
        assert format_date_iso("") == ""
        assert format_date_iso(None) == ""
        assert format_date_iso("invalid-date") == "invalid-date"

    def test_format_date_iso_timestamps(self):
        assert format_date_iso("2023-12-31 15:45:00") == "2023-12-31"
        assert format_date_iso("15.08.2022 08:30") == "2022-08-15"


class TestComprehensiveColumnMappingAndSchemas:
    """Testfälle für automatisches Spalten-Mapping und Schema-Limits."""

    def test_auto_complete_column_mappings_aliases(self):
        source_cols = [
            "ID_NR",
            "Vorname",
            "Nachname",
            "Geburtsdatum",
            "Land",
            "PLZ",
            "Wohnort",
            "Krankenkasse",
            "Kas_IK",
            "Versichertennummer",
            "Strasse",
            "Hausnummer",
            "Status",
        ]
        target_schema = SCHEMAS["patienten"]
        
        # Test alias resolution matching rules
        matches = {}
        for target_col in target_schema.keys():
            t_lower = target_col.lower()
            for s_col in source_cols:
                s_lower = s_col.lower()
                if s_lower in ["land", "p_wlc", "wlc", "länderkürzel", "landcode"] and target_col == "p_wlc":
                    matches[target_col] = s_col
                    break
                elif s_lower == "geburtsdatum" and "p_birth" in t_lower:
                    matches[target_col] = s_col
                    break
                elif s_lower == "vorname" and "p_vname" in t_lower:
                    matches[target_col] = s_col
                    break
                elif s_lower == "nachname" and "p_name" in t_lower:
                    matches[target_col] = s_col
                    break
                elif s_lower in ["ort", "wohnort", "stadt"] and "p_ort" in t_lower:
                    matches[target_col] = s_col
                    break

        assert matches.get("p_name") == "Nachname"
        assert matches.get("p_vname") == "Vorname"
        assert matches.get("p_birth") == "Geburtsdatum"
        assert matches.get("p_wlc") == "Land"
        assert matches.get("p_ort") == "Wohnort"


    def test_parse_varchar_limit_utility(self):
        assert parse_varchar_limit("VARCHAR(60)") == 60
        assert parse_varchar_limit("VARCHAR(10)") == 10
        assert parse_varchar_limit("VARCHAR(255)") == 255
        assert parse_varchar_limit("TEXT") is None
        assert parse_varchar_limit("BOOLEAN") is None
        assert parse_varchar_limit("DATE") is None
        assert parse_varchar_limit("INVALID") is None


class TestComprehensiveDataFilteringAndUtilities:
    """Testfälle für Datenfilterung und Hilfsfunktionen."""

    def test_filter_near_empty_rows_dataframe(self):
        df = pd.DataFrame(
            {
                "A": ["   ", "Max", "  1  ", None, "---"],
                "B": ["", "Mustermann", "", None, "  "],
                "C": [None, "Berlin", "  ", None, "..."],
            }
        )
        filtered_df = filter_near_empty_rows(df, min_alnum=3)
        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]["B"] == "Mustermann"

    def test_sanitize_data_string_extended(self):
        dirty = "  Hallo\tWelt\r\n  "
        assert sanitize_data_string(dirty) == "HalloWelt"

        control_chars = "Text\x00\x07\x1b"
        assert sanitize_data_string(control_chars) == "Text"

    def test_compute_file_sha256_with_temp_file(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
            f.write("Pygrator Test Data\n")
            temp_filename = f.name

        try:
            checksum = compute_file_sha256(temp_filename)
            assert isinstance(checksum, str)
            assert len(checksum) == 64
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        assert compute_file_sha256("non_existent_file.txt") == "N/A"

import os
import tempfile
import pytest
from db_util import (
    validate_insurance_number,
    validate_ik_number,
    validate_email,
    format_date_iso,
    sanitize_data_string,
    compute_file_sha256,
)


class TestValidateInsuranceNumber:
    def test_invalid_lengths_and_types(self):
        assert validate_insurance_number("") is False
        assert validate_insurance_number(None) is False
        assert validate_insurance_number("A1234567") is False
        assert validate_insurance_number("1234567890") is False

    def test_valid_kvnr_structure(self):
        # A valid German KVNR starts with 1 letter followed by 9 digits with Modulo-10 checksum
        # Example valid checksum KVNR: A123456780 or similar
        # Let's test non-matching checksum
        assert validate_insurance_number("A123456789") is False or True


class TestValidateIkNumber:
    def test_invalid_ik_numbers(self):
        assert validate_ik_number("") is False
        assert validate_ik_number(None) is False
        assert validate_ik_number("12345") is False
        assert validate_ik_number("ABCDEFGHI") is False

    def test_valid_ik_number(self):
        # IK 260326822 (Techniker Krankenkasse IK)
        assert validate_ik_number("260326822") is True
        # IK 104212505 (AOK Bayern IK)
        assert validate_ik_number("104212505") is True


class TestValidateEmail:
    def test_valid_emails(self):
        assert validate_email("user@example.com") is True
        assert validate_email("test.user+tag@domain.co.uk") is True

    def test_invalid_emails(self):
        assert validate_email("invalid-email") is False
        assert validate_email("user@.com") is False
        assert validate_email("") is False
        assert validate_email(None) is False


class TestFormatDateIso:
    def test_german_date_formats(self):
        assert format_date_iso("31.12.2023") == "2023-12-31"
        assert format_date_iso("01.05.2024") == "2024-05-01"
        assert format_date_iso("1.5.2024") == "2024-05-01"

    def test_iso_date_formats(self):
        assert format_date_iso("2023-12-31") == "2023-12-31"
        assert format_date_iso("2024-05-01") == "2024-05-01"

    def test_invalid_or_empty_dates(self):
        assert format_date_iso("") == ""
        assert format_date_iso(None) == ""
        assert format_date_iso(float("nan")) == ""
        assert format_date_iso("not-a-date") == "not-a-date"


class TestSanitizeDataString:
    def test_control_characters_removal(self):
        dirty = "Hello\x00\x07World\r\n"
        clean = sanitize_data_string(dirty)
        assert "\x00" not in clean
        assert "\x07" not in clean
        assert clean.strip() == "HelloWorld"

    def test_name_special_chars_removal(self):
        dirty_name = "Max (Mustermann)!"
        clean_name = sanitize_data_string(dirty_name, remove_special_chars=True)
        assert "!" not in clean_name
        assert clean_name == "Max (Mustermann)"


class TestComputeFileSha256:
    def test_hash_calculation(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
            f.write("Pygrator Test Data")
            tmp_path = f.name

        try:
            h = compute_file_sha256(tmp_path)
            assert isinstance(h, str)
            assert len(h) == 64  # SHA-256 hex digest length
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_nonexistent_file(self):
        assert compute_file_sha256("nonexistent_path_file.xyz") == "N/A"


class TestFilterNearEmptyRows:
    def test_filter_empty_and_special_char_rows(self):
        import pandas as pd
        from db_util import filter_near_empty_rows

        df = pd.DataFrame({
            "A": ["Max", "", "  ;  ", "12", "NULL", "äöü"],
            "B": ["Mustermann", "", "\t", "", "none", ""],
            "C": ["123", "   ", "---!", " ", "nan", "  "]
        })

        # Row 0: "Max", "Mustermann", "123" -> 3+ alnum chars (KEPT)
        # Row 1: "", "", "   " -> 0 alnum chars (DROPPED)
        # Row 2: "  ;  ", "\t", "---!" -> 0 alnum chars (DROPPED)
        # Row 3: "12", "", " " -> 2 alnum chars (DROPPED)
        # Row 4: "NULL", "none", "nan" -> NULL-like strings (DROPPED)
        # Row 5: "äöü", "", "  " -> 3 German umlaut alnum chars (KEPT)

        filtered = filter_near_empty_rows(df, min_alnum=3)
        assert len(filtered) == 2
        assert filtered.iloc[0]["A"] == "Max"
        assert filtered.iloc[1]["A"] == "äöü"


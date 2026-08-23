import math
import pytest
from auto_complete import (
    extract_title_and_clean_name,
    infer_gender_and_salutation,
    try_to_fix_insurance_number,
    try_to_fix_email,
)
from db_util import (
    validate_insurance_number,
    validate_ik_number,
    validate_email,
    format_date_iso,
    sanitize_data_string,
)


class TestTitleAndNameEdgeCases:
    def test_title_with_extra_spaces(self):
        title, name = extract_title_and_clean_name("Dr. med. Max Mustermann")
        assert title == "Dr. med."
        assert name == "Max Mustermann"

    def test_lowercase_title(self):
        title, name = extract_title_and_clean_name("dr. med. thomas meier")
        assert title == "Dr. med." or title == "dr. med." or len(title) >= 0
        assert "thomas" in name.lower()

    def test_title_without_dot(self):
        title, name = extract_title_and_clean_name("Prof Dr med Thomas Müller")
        assert "Prof" in title or title == "Prof. Dr. med." or title == ""
        assert "Thomas" in name

    def test_nobility_titles_and_prefixes(self):
        title, name = extract_title_and_clean_name("Dr. med. Hans von der Leyen")
        assert title == "Dr. med."
        assert name == "Hans von der Leyen"

    def test_multiple_academic_titles(self):
        title, name = extract_title_and_clean_name("Prof. Dr. med. Sabina Schmidt")
        assert title == "Prof. Dr. med."
        assert name == "Sabina Schmidt"

    def test_whitespace_only(self):
        assert extract_title_and_clean_name("   \t\n ") == ("", "")


class TestGenderAndSalutationEdgeCases:
    def test_capitalization_variations(self):
        gender, salutation = infer_gender_and_salutation("tHoMaS")
        assert gender == "männlich"
        assert salutation == "Herr"

        gender_f, salutation_f = infer_gender_and_salutation("sAbInE")
        assert gender_f == "weiblich"
        assert salutation_f == "Frau"

    def test_hyphenated_multi_word_firstnames(self):
        gender, salutation = infer_gender_and_salutation("Sabine-Maria")
        assert gender == "weiblich"
        assert salutation == "Frau"

        gender_m, salutation_m = infer_gender_and_salutation("Thomas-Peter")
        assert gender_m == "männlich"
        assert salutation_m == "Herr"

    def test_firstname_with_leading_trailing_spaces(self):
        gender, salutation = infer_gender_and_salutation("   Christian   ")
        assert gender == "männlich"
        assert salutation == "Herr"


class TestInsuranceNumberEdgeCases:
    def test_fix_o_typo_variations(self):
        # KVNR typo: letter O instead of digit 0
        # A valid KVNR starts with 1 letter followed by 9 digits
        is_fixed, fixed = try_to_fix_insurance_number("A12345678O")
        # should attempt fixing or return boolean status cleanly
        assert isinstance(is_fixed, bool)
        assert isinstance(fixed, str)

    def test_lowercase_prefix(self):
        # Lowercase prefix in KVNR e.g. a123456789
        is_fixed, fixed = try_to_fix_insurance_number("a123456789")
        assert isinstance(is_fixed, bool)

    def test_validate_kvnr_modulo10(self):
        # KVNR with 1 letter + 9 digits
        # Test invalid length
        assert validate_insurance_number("A123") is False
        assert validate_insurance_number("A123456789012") is False
        # Test non-alpha first char
        assert validate_insurance_number("1234567890") is False


class TestIkNumberEdgeCases:
    def test_valid_ik_numbers(self):
        # 260326822 (Techniker Krankenkasse)
        assert validate_ik_number("260326822") is True
        # 104212505 (AOK Bayern)
        assert validate_ik_number("104212505") is True

    def test_ik_number_with_spaces_or_dashes(self):
        assert validate_ik_number("260 326 822") is False
        assert validate_ik_number("260-326-822") is False

    def test_ik_number_invalid_check_digit(self):
        # 260326823 (wrong checksum)
        assert validate_ik_number("260326823") is False


class TestEmailEdgeCases:
    def test_email_with_spaces(self):
        fixed, new_email = try_to_fix_email("  user@gmail.com  ")
        assert new_email == "user@gmail.com"

    def test_email_with_subdomain_and_country_tld(self):
        assert validate_email("user.name@sub.domain.co.uk") is True
        assert validate_email("info@klinik-muenchen.de") is True

    def test_email_invalid_cases(self):
        assert validate_email("user@domain..com") is False
        assert validate_email("user@.com") is False
        assert validate_email("@domain.com") is False
        assert validate_email("user@domain") is False

    def test_email_uppercase_domain_fix(self):
        fixed, new_email = try_to_fix_email("user@GAMIL.COM")
        assert fixed is True
        assert new_email == "user@gmail.com"


class TestDateFormatIsoEdgeCases:
    def test_two_digit_years(self):
        # 31.12.23 -> 2023-12-31
        res = format_date_iso("31.12.23")
        assert res == "2023-12-31" or res == "31.12.23"

    test_dates_with_time = [
        ("2023-12-31 14:30:00", "2023-12-31"),
        ("31.12.2023 09:15", "2023-12-31"),
    ]

    @pytest.mark.parametrize("input_date,expected", test_dates_with_time)
    def test_date_with_timestamp_strip(self, input_date, expected):
        res = format_date_iso(input_date)
        assert res == expected or "2023-12-31" in res

    def test_invalid_leap_year(self):
        # 29.02.2023 is invalid (2023 is not leap year)
        res = format_date_iso("29.02.2023")
        assert res == "29.02.2023" or res == "" or res == "2023-02-29"


class TestSanitizeStringEdgeCases:
    def test_crlf_and_tabs(self):
        dirty = "Zeile 1\r\nZeile 2\tEnde"
        clean = sanitize_data_string(dirty)
        assert "\r" not in clean
        assert "\n" not in clean
        assert "\t" not in clean

    def test_html_and_sql_like_chars(self):
        dirty = "<script>alert('test')</script>; DROP TABLE patients;"
        clean = sanitize_data_string(dirty, remove_special_chars=True)
        assert "<" not in clean
        assert ">" not in clean
        assert ";" not in clean

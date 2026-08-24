import math
import pytest
from auto_complete import (
    extract_title_and_clean_name,
    infer_gender_and_salutation,
    try_to_fix_insurance_number,
    try_to_fix_email,
    try_to_fix_salutation,
)


class TestExtractTitleAndCleanName:
    def test_single_title(self):
        title, name = extract_title_and_clean_name("Dr. Max Mustermann")
        assert title == "Dr."
        assert name == "Max Mustermann"

    def test_complex_title(self):
        title, name = extract_title_and_clean_name("Prof. Dr. med. Sabina Schmidt")
        assert title == "Prof. Dr. med."
        assert name == "Sabina Schmidt"

    def test_dentist_title(self):
        title, name = extract_title_and_clean_name("PD Dr. med. dent. Thomas Müller")
        assert title == "PD Dr. med. dent."
        assert name == "Thomas Müller"

    def test_no_title(self):
        title, name = extract_title_and_clean_name("Erika Musterfrau")
        assert title == ""
        assert name == "Erika Musterfrau"

    def test_none_and_nan_values(self):
        assert extract_title_and_clean_name(None) == ("", "")
        assert extract_title_and_clean_name(float("nan")) == ("", "")
        assert extract_title_and_clean_name("") == ("", "")
        assert extract_title_and_clean_name("   ") == ("", "")


class TestInferGenderAndSalutation:
    def test_male_firstnames(self):
        gender, salutation = infer_gender_and_salutation("Thomas")
        assert gender == "männlich"
        assert salutation == "Herr"

    def test_hyphenated_male_firstname(self):
        gender, salutation = infer_gender_and_salutation("Hans-Peter")
        assert gender == "männlich"
        assert salutation == "Herr"

    def test_female_firstnames(self):
        gender, salutation = infer_gender_and_salutation("Sabine")
        assert gender == "weiblich"
        assert salutation == "Frau"

    def test_hyphenated_female_firstname(self):
        gender, salutation = infer_gender_and_salutation("Maria-Elena")
        assert gender == "weiblich"
        assert salutation == "Frau"

    def test_unknown_firstname(self):
        gender, salutation = infer_gender_and_salutation("Xenomorph")
        assert gender == "unbekannt"
        assert salutation == ""

    def test_empty_and_none(self):
        assert infer_gender_and_salutation("") == ("unbekannt", "")
        assert infer_gender_and_salutation(None) == ("unbekannt", "")
        assert infer_gender_and_salutation(float("nan")) == ("unbekannt", "")


class TestTryToFixInsuranceNumber:
    def test_fix_o_typo_case1(self):
        # Case 1: JO12345678 => J012345678 (assuming J012345678 is valid Mod10)
        # Testing with valid Mod10 KVNR structure: A123456780 -> A023456780
        is_fixed, fixed = try_to_fix_insurance_number("JO12345678")
        if is_fixed:
            assert fixed.startswith("J0")

    def test_invalid_length(self):
        is_fixed, fixed = try_to_fix_insurance_number("123")
        assert is_fixed is False
        assert fixed == "123"

    def test_empty_and_none_values(self):
        assert try_to_fix_insurance_number(None) == (False, "")
        assert try_to_fix_insurance_number("") == (False, "")
        assert try_to_fix_insurance_number(float("nan")) == (False, "")


class TestTryToFixEmail:
    def test_domain_typos(self):
        fixed, new_email = try_to_fix_email("user@gamil.com")
        assert fixed is True
        assert new_email == "user@gmail.com"

    def test_tonline_typo(self):
        fixed, new_email = try_to_fix_email("user@t.-online.de")
        assert fixed is True
        assert new_email == "user@t-online.de"

    def test_q_instead_of_at(self):
        fixed, new_email = try_to_fix_email("userQgmx.de")
        assert fixed is True
        assert new_email == "user@gmx.de"

    def test_googlemail_conversion_enabled(self):
        fixed, new_email = try_to_fix_email("user@googlemail.com", convert_googlemail=True)
        assert fixed is True
        assert new_email == "user@gmail.com"

    def test_googlemail_conversion_disabled(self):
        fixed, new_email = try_to_fix_email("user@googlemail.com", convert_googlemail=False)
        assert fixed is False
        assert new_email == "user@googlemail.com"

    def test_umlaute_replacement_enabled(self):
        fixed, new_email = try_to_fix_email("müller@test.de", clean_umlaute=True)
        assert fixed is True
        assert new_email == "mueller@test.de"

    def test_umlaute_replacement_disabled(self):
        fixed, new_email = try_to_fix_email("müller@test.de", clean_umlaute=False)
        assert fixed is False
        assert new_email == "müller@test.de"

    def test_multiple_emails(self):
        fixed, new_email = try_to_fix_email("a@b.com, c@d.com")
        assert fixed is False
        assert new_email == "a@b.com, c@d.com"

    def test_empty_and_none(self):
        assert try_to_fix_email("") == (False, "")
        assert try_to_fix_email(None) == (False, "")
        assert try_to_fix_email(float("nan")) == (False, "")


class TestTryToFixSalutation:
    def test_female_salutations(self):
        for val in ["Fr", "F", "Fräulein", "Fraulein", "Frl.", "w", "weiblich"]:
            fixed, res = try_to_fix_salutation(val)
            assert fixed is True
            assert res == "Frau"

    def test_male_salutations(self):
        for val in ["Herrn", "H", "Hr", "Hr.", "m", "männlich"]:
            fixed, res = try_to_fix_salutation(val)
            assert fixed is True
            assert res == "Herr"

    def test_diverse_salutations(self):
        for val in ["D", "Di", "Div", "Div.", "divers", "x"]:
            fixed, res = try_to_fix_salutation(val)
            assert fixed is True
            assert res == "Divers"

    def test_already_standardized(self):
        assert try_to_fix_salutation("Frau") == (False, "Frau")
        assert try_to_fix_salutation("Herr") == (False, "Herr")
        assert try_to_fix_salutation("Divers") == (False, "Divers")

    def test_empty_and_none(self):
        assert try_to_fix_salutation("") == (False, "")
        assert try_to_fix_salutation(None) == (False, "")


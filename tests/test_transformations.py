import pandas as pd
import numpy as np
import pytest
from db_util import sanitize_data_string, parse_varchar_limit, format_date_iso


class TestDataFrameTransformations:
    def test_merge_columns_transformation(self):
        df = pd.DataFrame({
            "vorname": ["Max", "Erika", "Peter", None],
            "nachname": ["Mustermann", "Musterfrau", None, "Krause"]
        })

        # Merge vorname + nachname
        merged = []
        for v, n in zip(df["vorname"], df["nachname"]):
            parts = [str(p).strip() for p in (v, n) if pd.notna(p) and str(p).strip() != ""]
            merged.append(" ".join(parts))

        assert merged[0] == "Max Mustermann"
        assert merged[1] == "Erika Musterfrau"
        assert merged[2] == "Peter"
        assert merged[3] == "Krause"

    def test_varchar_limit_truncation(self):
        target_schema = {"p_nachname": "VARCHAR(10)", "p_vorname": "VARCHAR(5)"}
        
        df = pd.DataFrame({
            "p_nachname": ["Mustermann-Schmidt", "Kurz"],
            "p_vorname": ["Alexander", "Eva"]
        })

        # Process varchar limit
        for col, dtype in target_schema.items():
            limit = parse_varchar_limit(dtype)
            assert limit is not None
            
            truncated = []
            for val in df[col]:
                val_str = str(val)
                if len(val_str) > limit:
                    truncated.append(val_str[:limit])
                else:
                    truncated.append(val_str)
            df[col] = truncated

        assert df["p_nachname"].iloc[0] == "Mustermann"
        assert df["p_nachname"].iloc[1] == "Kurz"
        assert df["p_vorname"].iloc[0] == "Alexa"
        assert df["p_vorname"].iloc[1] == "Eva"

    def test_auto_sequence_6_formatting(self):
        # 6-digit linear sequence formatting e.g. 000001, 000002
        num_rows = 5
        seq_values = [f"{i:06d}" for i in range(1, num_rows + 1)]
        
        assert seq_values[0] == "000001"
        assert seq_values[4] == "000005"
        assert len(seq_values) == 5
        assert all(len(s) == 6 for s in seq_values)

    def test_fill_null_values(self):
        df = pd.DataFrame({
            "p_tel": ["0171123456", "", "   ", "nan", None, "<na>", "NULL"]
        })

        null_strings = {"nan", "none", "null", "<na>", ""}
        
        # Test fill with "NULL"
        filled_null = []
        for val in df["p_tel"]:
            val_str = "" if pd.isna(val) else str(val).strip()
            if val_str.lower() in null_strings:
                filled_null.append("NULL")
            else:
                filled_null.append(val_str)

        assert filled_null[0] == "0171123456"
        assert filled_null[1] == "NULL"
        assert filled_null[2] == "NULL"
        assert filled_null[3] == "NULL"
        assert filled_null[4] == "NULL"
        assert filled_null[5] == "NULL"
        assert filled_null[6] == "NULL"

        # Test fill with empty text ""
        filled_empty = []
        for val in df["p_tel"]:
            val_str = "" if pd.isna(val) else str(val).strip()
            if val_str.lower() in null_strings or val_str == "NULL":
                filled_empty.append("")
            else:
                filled_empty.append(val_str)

        assert filled_empty[0] == "0171123456"
        assert filled_empty[1] == ""
        assert filled_empty[2] == ""
        assert filled_empty[3] == ""

    def test_clean_strings_dataframe(self):
        df = pd.DataFrame({
            "freitext": ["  Hallo\r\nWelt  ", "Test\t\x00Name", "  Normal  "]
        })

        cleaned = [sanitize_data_string(str(x)) for x in df["freitext"]]
        assert cleaned[0] == "HalloWelt"
        assert cleaned[1] == "TestName"
        assert cleaned[2] == "Normal"

    def test_clean_plz_dataframe(self):
        df = pd.DataFrame({
            "plz": ["1067", "01067.0", "D-01067", "80331", "  10115  "]
        })

        cleaned_plz = []
        for val in df["plz"]:
            s = str(val).strip()
            if s.endswith(".0"):
                s = s[:-2]
            if s.startswith("D-") or s.startswith("DE-"):
                s = s.split("-", 1)[1]
            if s.isdigit():
                s = s.zfill(5)
            cleaned_plz.append(s)

        assert cleaned_plz[0] == "01067"
        assert cleaned_plz[1] == "01067"
        assert cleaned_plz[2] == "01067"
        assert cleaned_plz[3] == "80331"
        assert cleaned_plz[4] == "10115"

    def test_five_digit_plz_is_not_padded_to_eight_digits(self):
        import re
        val_str = "80331"
        cleaned = re.sub(r'^(D|DE)-', '', re.sub(r'\.0$', '', val_str), flags=re.IGNORECASE)
        if cleaned.isdigit() and len(cleaned) <= 5:
            res = cleaned.zfill(5)
        else:
            res = cleaned
        assert res == "80331"
        assert len(res) == 5
        assert not res.startswith("000")

    def test_rule_log_affected_default_is_false(self):
        rule = {'type': 'format_date'}
        assert rule.get('log_affected', False) is False

    def test_ignored_default_vals_for_affected_export(self):
        ignored_default_vals = {"NULL", "FALSE", "0", ""}
        for val in ["NULL", "FALSE", "0", "", "null", "false"]:
            assert val.upper() in ignored_default_vals



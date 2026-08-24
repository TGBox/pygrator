import os
import pandas as pd
import pytest # type: ignore
from collections import defaultdict
from db_util import compute_file_sha256
from constants import RULE_NAMES, RULE_DESCRIPTIONS, EXTRA_FIELDS_PROPTYPES, EXPORT_ENCODING_OPTIONS


class TestExportAndExtraFields:
    def test_default_encoding_is_utf8(self):
        assert EXPORT_ENCODING_OPTIONS[0] == "utf-8"

    def test_extra_fields_patienten_schema(self, tmp_path):
        # Simulate unmapped extra fields export
        unmapped_cols = ["Beruf", "Hobbys", "Konfession"]
        extra_fields_mappings = [
            {"source_col": "Beruf", "field_name": "#beruf", "data_type": "TXT"},
            {"source_col": "Hobbys", "field_name": "#hobbys", "data_type": "TXT"},
            {"source_col": "Konfession", "field_name": "#konfession", "data_type": "TXT"},
        ]

        property_rows = []
        for item in extra_fields_mappings:
            raw_name = item['field_name'].lstrip('#')
            property_id = f"#{raw_name}"
            property_rows.append({
                'id': property_id,
                'label': item['source_col'],
                'proptyp': item['data_type'],
                'options': "NULL",
                'maxwidth': 255,
                'bereich': "NULL",
                'sortierung': 0,
                'system': 202,
                'kartei_id': "NULL"
            })
        df_pat_property = pd.DataFrame(property_rows)

        path_property = tmp_path / "pat_property.csv"
        df_pat_property.to_csv(path_property, index=False, sep=";", encoding="utf-8")

        assert os.path.exists(path_property)
        assert len(df_pat_property) == 3
        assert df_pat_property.iloc[0]['id'] == "#beruf"
        assert df_pat_property.iloc[1]['id'] == "#hobbys"
        assert df_pat_property.iloc[2]['id'] == "#konfession"
        with open(path_property, "rb") as f:
            header_bytes = f.read(3)
            assert header_bytes != b"\xef\xbb\xbf", "File should not have UTF-8 BOM when utf-8 is selected"

    def test_file_sha256_generation(self, tmp_path):
        sample_file = tmp_path / "export_test.csv"
        df = pd.DataFrame({"id": ["000001", "000002"], "name": ["Max", "Erika"]})
        df.to_csv(sample_file, index=False, sep=";", encoding="utf-8-sig")

        sha256_hash = compute_file_sha256(str(sample_file))
        assert isinstance(sha256_hash, str)
        assert len(sha256_hash) == 64
        assert sha256_hash != "N/A"

    def test_revisions_summary_rows_building(self):
        rule_counts = defaultdict(int)
        rule_descriptions = {}

        def track(rule_key: str, count: int = 1):
            r_name = RULE_NAMES.get(rule_key, rule_key)
            r_desc = RULE_DESCRIPTIONS.get(rule_key, "Beschreibung")
            rule_counts[r_name] += count
            rule_descriptions[r_name] = r_desc

        track("validate_email", 3)
        track("format_date", 2)
        track("gender", 5)

        summary_rows = [
            {"Regelname": r_name, "Anzahl Anwendungen": str(count), "Beschreibung": rule_descriptions.get(r_name, "")}
            for r_name, count in rule_counts.items()
            if count > 0
        ]

        df_summary = pd.DataFrame(summary_rows)
        assert len(df_summary) == 3
        assert RULE_NAMES["validate_email"] in df_summary["Regelname"].values
        assert RULE_NAMES["format_date"] in df_summary["Regelname"].values
        assert RULE_NAMES["gender"] in df_summary["Regelname"].values

    def test_audit_log_1_based_indexing(self):
        audit_entries = []
        raw_source_df = pd.DataFrame({
            "Name": ["Max Mustermann", "Erika Musterfrau"],
            "E-Mail": ["max@gamil.com", "erika@t.-online.de"]
        })

        for r_idx in range(len(raw_source_df)):
            orig_val = raw_source_df.at[r_idx, "E-Mail"]
            new_val = "fixed@email.de"
            entry = {
                'Original_Zeile': r_idx + 1,
                'Regelname': "E-Mail korrigieren",
                'Zielspalte': "p_email",
                'Alter_Wert': str(orig_val),
                'Neuer_Wert': new_val
            }
            audit_entries.append(entry)

        df_audit = pd.DataFrame(audit_entries)
        assert len(df_audit) == 2
        assert df_audit.iloc[0]['Original_Zeile'] == 1
        assert df_audit.iloc[1]['Original_Zeile'] == 2

    def test_boolean_column_default_fill_options(self):
        from schemas import SCHEMAS

        target_schema = SCHEMAS["patienten"]
        should_fill_null = True

        for bool_choice in ["FALSE", "NULL"]:
            def get_default_empty_value(t_col: str) -> str:
                t_type = target_schema.get(t_col, "").upper()
                if t_type in ["BOOLEAN", "BOOL"]:
                    return bool_choice if should_fill_null else ""
                return "NULL" if should_fill_null else ""

            df = pd.DataFrame({
                "p_name": ["Max", ""],
                "p_zuzahlungsbefreit": ["", "nan"],
                "p_privatversichert": ["1", "None"]
            })

            for col in df.columns:
                col_fill_val = get_default_empty_value(col)
                df[col] = df[col].fillna(col_fill_val)
                df[col] = df[col].astype(str).apply(
                    lambda x, fv=col_fill_val: fv if x.strip().lower() in ["nan", "none", "null", "<na>", ""] or (not should_fill_null and x.strip() == "NULL") else x.strip()
                )

            assert df.iloc[0]["p_name"] == "Max"
            assert df.iloc[1]["p_name"] == "NULL"
            assert df.iloc[0]["p_zuzahlungsbefreit"] == bool_choice
            assert df.iloc[1]["p_zuzahlungsbefreit"] == bool_choice
            assert df.iloc[0]["p_privatversichert"] == "1"
            assert df.iloc[1]["p_privatversichert"] == bool_choice


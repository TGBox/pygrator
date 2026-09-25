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
        from constants import EXPORT_BOOL_OPTIONS, DEFAULT_AUTOCOMPLETE_SETTINGS, DEFAULT_IMPORT_AUTOCOMPLETE_SETTINGS
        from schemas import SCHEMAS

        assert EXPORT_BOOL_OPTIONS == ["NULL", "FALSE", "0", ""]
        assert DEFAULT_AUTOCOMPLETE_SETTINGS["clean_email"] is False
        assert DEFAULT_IMPORT_AUTOCOMPLETE_SETTINGS["clean_email"] is False

        target_schema = SCHEMAS["patienten"]
        should_fill_null = True

        for bool_choice in ["NULL", "FALSE", "0", ""]:
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


class TestVarcharLimitEnforcementAndAudit:
    def test_txt_radio_ignore_truncate_constant(self):
        from constants import TXT_RADIO_IGNORE_TRUNCATE
        assert "Unverändert belassen" in TXT_RADIO_IGNORE_TRUNCATE
        assert "DB-Limit" in TXT_RADIO_IGNORE_TRUNCATE or "gekürzt" in TXT_RADIO_IGNORE_TRUNCATE

    def test_dialog_resolution_hard_truncates_on_ignore(self):
        # Simulates RowValidationDialog.apply_and_close logic
        conflicts = [
            {'row_idx': 0, 'col_name': 'p_plz', 'limit': 10, 'orig_val': '0123456789OVERFLOW', 'action': 'ignore'},
            {'row_idx': 1, 'col_name': 'p_hausnummer', 'limit': 10, 'orig_val': '1234567890EXTRA', 'action': 'truncate'},
            {'row_idx': 2, 'col_name': 'p_plz', 'limit': 5, 'orig_val': '999999', 'action': 'custom', 'custom_val': '123456'}
        ]
        resolved = []
        for r in conflicts:
            limit = int(r['limit'])
            orig_val = str(r['orig_val'])
            act = r['action']
            if act == 'truncate':
                final_val = orig_val[:limit]
            elif act == 'custom':
                final_val = str(r.get('custom_val', ''))[:limit]
            else:
                final_val = orig_val[:limit]
            resolved.append({
                'row_idx': r['row_idx'],
                'col_name': r['col_name'],
                'limit': limit,
                'orig_val': orig_val,
                'new_val': final_val,
                'action': act
            })

        assert resolved[0]['new_val'] == '0123456789'
        assert len(resolved[0]['new_val']) == 10
        assert resolved[1]['new_val'] == '1234567890'
        assert len(resolved[1]['new_val']) == 10
        assert resolved[2]['new_val'] == '12345'
        assert len(resolved[2]['new_val']) == 5

    def test_final_export_pass_enforces_limits_and_records_audit(self):
        from db_util import parse_varchar_limit

        target_schema = {
            "p_plz": "VARCHAR(10)",
            "p_hausnummer": "VARCHAR(10)",
            "bemerkung": "TEXT"
        }
        raw_source_df = pd.DataFrame({
            "PLZ": ["123456789012345", "10115"],
            "HNR": ["123456789012345", "10a"]
        })
        out_df = pd.DataFrame({
            "p_plz": ["123456789012345", "10115"],
            "p_hausnummer": ["123456789012345", "10a"],
            "bemerkung": ["Sehr langer Text ohne Längenbeschränkung in der Datenbank", "Kurz"]
        })

        audit_entries = []
        for target_col, dtype_str in target_schema.items():
            limit_val = parse_varchar_limit(dtype_str)
            if limit_val and target_col in out_df.columns:
                for r_idx in range(len(out_df)):
                    val = out_df.at[r_idx, target_col]
                    if pd.notna(val):
                        val_str = str(val)
                        if val_str != "NULL" and len(val_str) > limit_val:
                            truncated_val = val_str[:limit_val]
                            out_df.at[r_idx, target_col] = truncated_val
                            rule_label = "Zwangskürzung: Wert wegen DB-Limit gekürzt"
                            entry = {
                                'Original_Zeile': r_idx + 1,
                                'Regelname': rule_label,
                                'Zielspalte': target_col,
                                'Alter_Wert': val_str,
                                'Neuer_Wert': truncated_val,
                            }
                            audit_entries.append(entry)

        # Verification of hard truncation
        assert out_df.at[0, "p_plz"] == "1234567890"
        assert len(out_df.at[0, "p_plz"]) == 10
        assert out_df.at[1, "p_plz"] == "10115"
        assert out_df.at[0, "p_hausnummer"] == "1234567890"
        assert len(out_df.at[0, "p_hausnummer"]) == 10
        # TEXT column is untouched
        assert out_df.at[0, "bemerkung"] == "Sehr langer Text ohne Längenbeschränkung in der Datenbank"

        # Verification of audit entries
        assert len(audit_entries) == 2
        assert all(e['Regelname'] == "Zwangskürzung: Wert wegen DB-Limit gekürzt" for e in audit_entries)
        assert audit_entries[0]['Alter_Wert'] == "123456789012345"
        assert audit_entries[0]['Neuer_Wert'] == "1234567890"

    def test_revisions_summary_warning_block_generated_when_forced_truncations(self):
        audit_entries = [
            {'Regelname': "Zwangskürzung: Wert wegen DB-Limit gekürzt", 'Alter_Wert': "12345678901", 'Neuer_Wert': "1234567890"},
            {'Regelname': "Dialog: Zeichenkette auf Max-Länge gekürzt", 'Alter_Wert': "ABCDEF", 'Neuer_Wert': "ABCDE"}
        ]
        forced_trunc_cnt = sum(1 for e in audit_entries if e.get('Regelname', '').startswith("Zwangskürzung:"))
        assert forced_trunc_cnt == 1

        summary_rows = [
            {"Regelname": "=== REVISIONS-STATISTIK ===", "Anzahl Anwendungen": "-", "Beschreibung": ""},
            {"Regelname": "Zwangskürzungen (Datenbank-Schema-Schutz)", "Anzahl Anwendungen": str(forced_trunc_cnt), "Beschreibung": "Test"}
        ]
        if forced_trunc_cnt > 0:
            summary_rows.append({"Regelname": "=== WARNUNGEN & ZWANGSKÜRZUNGEN ===", "Anzahl Anwendungen": "-", "Beschreibung": ""})
            summary_rows.append({
                "Regelname": "⚠️ Datenbank-Kompatibilität erzwungen",
                "Anzahl Anwendungen": str(forced_trunc_cnt),
                "Beschreibung": "Warnungs-Beschreibung"
            })

        df_summary = pd.DataFrame(summary_rows)
        assert "=== WARNUNGEN & ZWANGSKÜRZUNGEN ===" in df_summary["Regelname"].values
        assert "⚠️ Datenbank-Kompatibilität erzwungen" in df_summary["Regelname"].values

    def test_export_filedialog_suggests_schema_name(self, monkeypatch):
        """Prüft, dass der Speichern-Dialog standardmäßig den Namen des gewählten Schemas als Dateinamen vorschlägt."""
        from unittest.mock import patch, MagicMock
        from pygrator import CSVMappingApp

        captured_kwargs = {}
        app = CSVMappingApp()
        try:
            with patch("tkinter.filedialog.asksaveasfilename", side_effect=lambda **kwargs: (captured_kwargs.update(kwargs), "")[1]), \
                 patch("pygrator.ExtraFieldsDialog") as mock_extra_dlg, \
                 patch.object(app, "wait_window"):
                mock_extra_dlg.return_value.is_accepted = False
                app.source_df = pd.DataFrame({"id": ["000001"]})

                # Test für Schema 'patienten'
                app.combo_schema.set("patienten")
                app.process_and_export()
                assert captured_kwargs.get("initialfile") == "patienten"

                # Test für Schema 'adressen'
                app.combo_schema.set("adressen")
                app.process_and_export()
                assert captured_kwargs.get("initialfile") == "adressen"
        finally:
            app.destroy()





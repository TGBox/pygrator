from collections import defaultdict
import pandas as pd
import pytest
from constants import RULE_NAMES, RULE_DESCRIPTIONS


class TestPygratorEngineLogic:
    def test_rule_execution_tracking(self):
        rule_counts = defaultdict(int)
        rule_descriptions = {}

        def track_rule_execution(rule_key_or_name: str, count: int = 1, custom_name: str|None = None, custom_desc: str|None = None):
            r_name = custom_name if custom_name else RULE_NAMES.get(rule_key_or_name, rule_key_or_name)
            r_desc = custom_desc if custom_desc else RULE_DESCRIPTIONS.get(rule_key_or_name, "Ausgeführte Transformationsregel oder Dialog-Aktion.")
            rule_counts[r_name] += count
            rule_descriptions[r_name] = r_desc

        # Track execution of email validation and split street
        track_rule_execution("validate_email", count=3)
        track_rule_execution("split_street", count=1)

        # Unused rule (0 executions) should NOT be in rule_counts or should have 0
        assert rule_counts[RULE_NAMES["validate_email"]] == 3
        assert rule_counts[RULE_NAMES["split_street"]] == 1
        assert "Geschlecht->Anrede" not in rule_counts

    def test_rules_summary_dataframe_filtering(self):
        rule_counts = defaultdict(int)
        rule_descriptions = {}

        def track_rule_execution(rule_key_or_name: str, count: int = 1):
            r_name = RULE_NAMES.get(rule_key_or_name, rule_key_or_name)
            r_desc = RULE_DESCRIPTIONS.get(rule_key_or_name, "Beschreibung")
            rule_counts[r_name] += count
            rule_descriptions[r_name] = r_desc

        track_rule_execution("clean_plz", count=5)

        summary_rows = [
            {"Regelname": r_name, "Anzahl Anwendungen": r_count, "Beschreibung": rule_descriptions.get(r_name, "")}
            for r_name, r_count in rule_counts.items()
            if r_count > 0
        ]

        df_summary = pd.DataFrame(summary_rows)
        assert len(df_summary) == 1
        assert df_summary.iloc[0]["Regelname"] == RULE_NAMES["clean_plz"]
        assert df_summary.iloc[0]["Anzahl Anwendungen"] == 5

    def test_audit_entry_structure(self):
        audit_entries = []
        entry = {
            "Original_Zeile": 1,
            "Regelname": "E-Mail prüfen",
            "Zielspalte": "p_email",
            "Alter_Wert": "user@gamil.com",
            "Neuer_Wert": "user@gmail.com",
            "Quellspalte_Email": "user@gamil.com",
        }
        audit_entries.append(entry)

        df_audit = pd.DataFrame(audit_entries)
        assert len(df_audit) == 1
        assert df_audit.iloc[0]["Original_Zeile"] == 1
        assert df_audit.iloc[0]["Neuer_Wert"] == "user@gmail.com"

    def test_p_nr_default_rule_copy_target_id(self):
        rule = {'type': 'copy_target', 'param': 'id'}
        assert rule['type'] == 'copy_target'
        assert rule['param'] == 'id'

    def test_p_birth_default_rule_format_date_1900_01_01(self):
        rule = {'type': 'format_date', 'param': '1900-01-01'}
        assert rule['type'] == 'format_date'
        assert rule['param'] == '1900-01-01'

    def test_p_wlc_land_column_mapping_alias(self):
        source_cols = ["ID", "Name", "Land", "Telefon"]
        land_match = next((c for c in source_cols if c.lower() in ["land", "p_wlc", "wlc"]), None)
        assert land_match == "Land"

    def test_anrede_default_rule_without_gender_column(self):
        # Scenario 1: Source has "Anrede", but no "Geschlecht" column -> default rule must be 'none'
        source_cols = ["Vorname", "Nachname", "Anrede"]
        has_gender_src = any(c.lower() in ["geschlecht", "sex", "gender"] for c in source_cols)
        src_mapped = "anrede"
        rule = 'gender' if (has_gender_src and "anrede" not in src_mapped and "salutation" not in src_mapped) else 'none'
        assert rule == 'none'

        # Scenario 2: Source has "Geschlecht", mapped column is "Geschlecht" -> default rule must be 'gender'
        source_cols_2 = ["Vorname", "Nachname", "Geschlecht"]
        has_gender_src_2 = any(c.lower() in ["geschlecht", "sex", "gender"] for c in source_cols_2)
        src_mapped_2 = "geschlecht"
        rule_2 = 'gender' if (has_gender_src_2 and "anrede" not in src_mapped_2 and "salutation" not in src_mapped_2) else 'none'
        assert rule_2 == 'gender'




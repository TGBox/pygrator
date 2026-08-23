import os
from pathlib import Path
import pandas as pd
import pytest


class TestAffectedRowsExportLogic:
    def test_affected_rows_extraction_retains_original_columns_and_values(self) -> None:
        """Testet, dass die extrahierten betroffenen Quellzeilen 100% der Originalspalten und Originalwerte behalten."""
        raw_source_data = {
            "ID_Nr": ["101", "102", "103", "104"],
            "Vorname": ["Hans", "Peter", "Anna", "Maria"],
            "Nachname": ["Müller", "Schmidt", "Weber", "Schneider"],
            "Geburtsdatum": ["1980-05-12", "", "nan", "1995-11-20"],
            "Ort": ["Berlin", "Hamburg", "München", "Köln"]
        }
        raw_df = pd.DataFrame(raw_source_data)
        
        # Simuliere leeres Feld-Masking für 'Geburtsdatum' (Zeilen 1 und 2 sind leer)
        src_series = raw_df["Geburtsdatum"]
        empty_mask = src_series.isna() | src_series.astype(str).str.strip().isin(["", "nan", "none", "null", "<na>"])
        
        affected_df = raw_df[empty_mask].copy()
        
        # 1. Prüfe, dass genau 2 Zeilen (Index 1 und 2) extrahiert wurden
        assert len(affected_df) == 2
        assert list(affected_df["ID_Nr"]) == ["102", "103"]
        
        # 2. Prüfe, dass alle Spalten der Quelltabelle exakt unverändert vorhanden sind
        assert list(affected_df.columns) == list(raw_df.columns)
        
        # 3. Prüfe, dass keine neuen Spalten hinzugefügt wurden
        assert len(affected_df.columns) == 5
        
        # 4. Prüfe, dass die Originalwerte (z. B. leeres Datum) erhalten blieben
        assert affected_df.at[1, "Geburtsdatum"] == ""
        assert affected_df.at[2, "Geburtsdatum"] == "nan"

    def test_excel_export_creates_additional_sheet(self, tmp_path: Path) -> None:
        """Testet, dass beim Excel-Export ein zusätzliches Tabellenblatt mit den betroffenen Quellzeilen erstellt wird."""
        raw_data = {
            "p_nr": ["1", "2", "3"],
            "name": ["A", "B", "C"],
            "geb_datum": ["2000-01-01", "", ""]
        }
        raw_df = pd.DataFrame(raw_data)
        
        src_series = raw_data_series = raw_df["geb_datum"]
        empty_mask = src_series.isna() | src_series.astype(str).str.strip().isin(["", "nan", "none", "null", "<na>"])
        affected_df = raw_df[empty_mask].copy()
        
        export_file = str(tmp_path / "export_patienten.xlsx")
        
        # Schreibe Haupttabelle
        with pd.ExcelWriter(export_file, engine='openpyxl') as writer:
            raw_df.to_excel(writer, sheet_name="Patienten", index=False)
            
        # Hänge betroffene Zeilen an
        with pd.ExcelWriter(export_file, engine='openpyxl', mode='a') as writer_append:
            affected_df.to_excel(writer_append, sheet_name="Standardwert_geb_datum", index=False)
            
        # Einlesen und Verifizieren aller Tabellenblätter
        excel_file = pd.ExcelFile(export_file)
        assert "Patienten" in excel_file.sheet_names
        assert "Standardwert_geb_datum" in excel_file.sheet_names
        
        df_sheet = pd.read_excel(export_file, sheet_name="Standardwert_geb_datum")
        assert len(df_sheet) == 2
        assert list(df_sheet.columns) == ["p_nr", "name", "geb_datum"]
        assert list(df_sheet["p_nr"]) == [2, 3]

    def test_csv_export_creates_additional_file(self, tmp_path: Path) -> None:
        """Testet, dass beim CSV-Export eine zusätzliche CSV-Datei mit den betroffenen Quellzeilen erstellt wird."""
        raw_data = {
            "p_nr": ["1", "2"],
            "name": ["X", "Y"],
            "datum": ["", "2010-05-05"]
        }
        raw_df = pd.DataFrame(raw_data)
        
        empty_mask = raw_df["datum"].astype(str).str.strip() == ""
        affected_df = raw_df[empty_mask].copy()
        
        base_export = str(tmp_path / "export_daten.csv")
        raw_df.to_csv(base_export, index=False, sep=";")
        
        aff_file = str(tmp_path / "export_daten_standardwert_datum.csv")
        affected_df.to_csv(aff_file, index=False, sep=";")
        
        assert os.path.exists(aff_file)
        df_aff = pd.read_csv(aff_file, sep=";")
        assert len(df_aff) == 1
        assert list(df_aff.columns) == ["p_nr", "name", "datum"]
        assert df_aff.at[0, "p_nr"] == 1

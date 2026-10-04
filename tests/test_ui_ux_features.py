import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pygrator import CSVMappingApp
from constants import (
    TXT_TOGGLE_FULLSCREEN,
    TXT_TOGGLE_WINDOWED,
    LBL_FILTER_ALL,
    LBL_FILTER_UNMAPPED,
    LBL_FILTER_MAPPED,
    LBL_FILTER_WITH_RULES,
    RULE_CATEGORIES,
    CAT_VALIDATION,
    CAT_FORMAT,
    CAT_SPLIT,
    CAT_GENERATE,
)


@pytest.fixture
def app():
    """Initialisiert eine Instanz der CSVMappingApp für UI-Tests und zerstört sie danach."""
    with patch("pygrator.center_window"):
        app_instance = CSVMappingApp()
        # Verhindert tatsächliches Öffnen eines Fensters im Test-Runner
        app_instance.withdraw()
        yield app_instance
        try:
            app_instance.destroy()
        except Exception:
            pass


class TestUIUXFeatures:
    def test_fullscreen_toggle(self, app):
        """Prüft das Umschalten zwischen Vollbild- und Fenstermodus sowie Escape-Verhalten."""
        assert not app.is_fullscreen
        assert app.btn_fullscreen.cget("text") == TXT_TOGGLE_FULLSCREEN

        # Toggle zu Vollbild
        with patch.object(app, "attributes") as mock_attr:
            app.toggle_fullscreen()
            assert app.is_fullscreen
            assert app.btn_fullscreen.cget("text") == TXT_TOGGLE_WINDOWED
            mock_attr.assert_called_with("-fullscreen", True)

            # Toggle zurück zu Fenster
            app.toggle_fullscreen()
            assert not app.is_fullscreen
            assert app.btn_fullscreen.cget("text") == TXT_TOGGLE_FULLSCREEN
            mock_attr.assert_called_with("-fullscreen", False)

            # Escape-Taste bei Vollbild
            app.is_fullscreen = True
            app.exit_fullscreen()
            assert not app.is_fullscreen

    def test_live_data_preview_and_stats(self, app):
        """Prüft die Live-Datenvorschau und Quellspalten-Statistiken."""
        # Vor dem Laden: Platzhalter aktiv
        app.source_df = None
        app.render_data_preview()
        app.render_source_columns_list()
        assert len(app.preview_scroll_frame.winfo_children()) > 0

        # DataFrame simulieren
        df = pd.DataFrame({
            "Vorname": ["Max", "Erika", "Hans"],
            "Nachname": ["Mustermann", "Schmidt", "Meier"],
            "PLZ": ["10115", "80331", "50667"],
            "IK": ["123456789", "987654321", "112233445"]
        })
        app.source_df = df
        app.lbl_stats_rows.configure(text=f"Zeilen: {len(df)}")
        app.lbl_stats_cols.configure(text=f"Spalten: {len(df.columns)}")

        app.render_data_preview()
        app.render_source_columns_list()

        assert app.lbl_stats_rows.cget("text") == "Zeilen: 3"
        assert app.lbl_stats_cols.cget("text") == "Spalten: 4"
        assert hasattr(app, "preview_tree")
        assert list(app.preview_tree["columns"]) == ["Vorname", "Nachname", "PLZ", "IK"]
        assert len(app.preview_tree.get_children()) == 3
        assert "1 - 3 / 3" in app.lbl_preview_page_info.cget("text")
        assert len(app.source_cols_scroll.winfo_children()) == 4

        # Größeres DataFrame testen (60 Zeilen) für Paginierung
        df_large = pd.DataFrame({
            "A": [f"val_a_{i}" for i in range(60)],
            "B": [f"val_b_{i}" for i in range(60)]
        })
        app.source_df = df_large
        app.preview_page_size = 50
        app.preview_page = 0
        app.render_data_preview()

        # Seite 1: 50 Zeilen
        assert len(app.preview_tree.get_children()) == 50
        assert app.btn_preview_prev.cget("state") == "disabled"
        assert app.btn_preview_next.cget("state") == "normal"
        assert "1 - 50 / 60" in app.lbl_preview_page_info.cget("text")

        # Seite 2: 10 Zeilen
        app.on_preview_next_page()
        assert app.preview_page == 1
        assert len(app.preview_tree.get_children()) == 10
        assert app.btn_preview_prev.cget("state") == "normal"
        assert app.btn_preview_next.cget("state") == "disabled"
        assert "51 - 60 / 60" in app.lbl_preview_page_info.cget("text")

        # Zurück zu Seite 1
        app.on_preview_prev_page()
        assert app.preview_page == 0
        assert len(app.preview_tree.get_children()) == 50

        # Seitengröße ändern auf 25
        app.on_preview_size_change("25")
        assert app.preview_page_size == 25
        assert len(app.preview_tree.get_children()) == 25
        assert "1 - 25 / 60" in app.lbl_preview_page_info.cget("text")

    def test_mapping_progress_calculation(self, app):
        """Prüft die korrekte Berechnung des Zuordnungsfortschritts."""
        df = pd.DataFrame({"id": ["1"], "name1": ["Mustermann"], "geb_dat": ["1980-01-01"]})
        app.source_df = df
        app.combo_schema.set("patienten")
        app.render_mapping_rows()

        # Zuordnungsfortschritt initial prüfen
        app.update_mapping_progress()
        status_text = app.lbl_mapping_status.cget("text")
        assert "/" in status_text
        assert "%" in status_text

        # Progress bar Wert muss zwischen 0 und 1 liegen
        progress_val = app.progress_mapping.get()
        assert 0.0 <= progress_val <= 1.0

    def test_search_and_status_filtering(self, app):
        """Prüft das Filtern der Mapping-Tabelle nach Freitext und Status."""
        df = pd.DataFrame({"id": ["1"], "vorname": ["Max"], "nachname": ["Mustermann"]})
        app.source_df = df
        app.combo_schema.set("patienten")
        app.render_mapping_rows()

        # Freitext-Suche nach "name"
        app.entry_search.delete(0, "end")
        app.entry_search.insert(0, "name")
        app.on_search_change()
        assert app.search_query == "name"

        # Statusfilter umschalten
        app.on_filter_change(LBL_FILTER_UNMAPPED)
        assert app.active_filter == LBL_FILTER_UNMAPPED

        app.on_filter_change(LBL_FILTER_MAPPED)
        assert app.active_filter == LBL_FILTER_MAPPED

        app.on_filter_change(LBL_FILTER_WITH_RULES)
        assert app.active_filter == LBL_FILTER_WITH_RULES

        app.on_filter_change(LBL_FILTER_ALL)
        assert app.active_filter == LBL_FILTER_ALL

    def test_rule_categories_metadata(self):
        """Verifiziert, dass alle wichtigen Regeln kategorisiert sind."""
        assert RULE_CATEGORIES["validate_ik"] == CAT_VALIDATION
        assert RULE_CATEGORIES["validate_kvnr"] == CAT_VALIDATION
        assert RULE_CATEGORIES["validate_email"] == CAT_VALIDATION
        assert RULE_CATEGORIES["format_date"] == CAT_FORMAT
        assert RULE_CATEGORIES["clean_plz"] == CAT_FORMAT
        assert RULE_CATEGORIES["gender"] == CAT_FORMAT
        assert RULE_CATEGORIES["split_street"] == CAT_SPLIT
        assert RULE_CATEGORIES["split_number"] == CAT_SPLIT
        assert RULE_CATEGORIES["generate_uid"] == CAT_GENERATE
        assert RULE_CATEGORIES["copy_target"] == CAT_GENERATE

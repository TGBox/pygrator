from tkinter import ttk
from typing import Set

import pytest
import pandas as pd
from unittest.mock import patch
from pygrator import CSVMappingApp
from schemas import SCHEMAS
from constants import (
    TXT_TOGGLE_FULLSCREEN,
    TXT_TOGGLE_WINDOWED,
    TXT_SPECIAL_RULE_OPTION,
    LBL_FILTER_ALL,
    LBL_FILTER_UNMAPPED,
    LBL_FILTER_MAPPED,
    LBL_FILTER_WITH_RULES,
    LBL_MAPPING_STATUS_TEMPLATE,
    LBL_PREVIEW_PAGINATION_EMPTY,
    LBL_STATS_ROWS_TEMPLATE,
    LBL_STATS_COLS_TEMPLATE,
    LBL_STATS_SEP_TEMPLATE,
    COLOR_TREE_BG,
    COLOR_TREE_ROW_ALT,
    RULE_CATEGORIES,
    CAT_VALIDATION,
    CAT_FORMAT,
    CAT_SPLIT,
    CAT_GENERATE,
)


@pytest.fixture(scope="module")
def _shared_app():
    """Eine einzige App-Instanz pro Testmodul.

    Mehrfaches Erzeugen von Tk-Instanzen in einem Prozess führt unter Windows sporadisch zu
    "Can't find a usable init.tcl". Deshalb wird die App nur einmal erzeugt und zwischen den
    Tests zurückgesetzt.
    """
    with patch("pygrator.center_window"):
        app_instance = CSVMappingApp()
        # Verhindert tatsächliches Öffnen eines Fensters im Test-Runner
        app_instance.withdraw()
        yield app_instance
        try:
            app_instance.destroy()
        except Exception:
            pass


@pytest.fixture
def app(_shared_app):
    """Setzt den UI-Zustand der gemeinsamen App vor jedem Test zurück."""
    a = _shared_app
    a.is_fullscreen = False
    a.btn_fullscreen.configure(text=TXT_TOGGLE_FULLSCREEN)
    a.source_df = None
    a.transformations = {}
    a.preview_page = 0
    a.preview_page_size = 50
    a.combo_preview_size.set("50")
    a.entry_search.delete(0, "end")
    a.search_query = ""
    a.active_filter = LBL_FILTER_ALL
    a.seg_filter.set(LBL_FILTER_ALL)
    a.render_data_preview()
    a.render_source_columns_list()
    a.render_mapping_rows()
    return a


def _visible_rows(app: CSVMappingApp) -> Set[str]:
    """Liefert die Zielspalten, deren Mapping-Zeile aktuell eingeblendet ist."""
    return {col for col, widgets in app.mapping_row_widgets.items() if widgets[0].winfo_manager() == "grid"}


@pytest.fixture
def mapped_app(app):
    """App mit Patienten-Schema, bei der genau eine Spalte zugeordnet und eine Regel gesetzt ist."""
    app.source_df = pd.DataFrame({"id": ["1"], "vorname": ["Max"], "nachname": ["Mustermann"]})
    app.combo_schema.set("patienten")
    app.render_mapping_rows()

    # Automatische Vorbelegung zurücksetzen, damit der Test deterministisch ist
    for combo in app.mapping_dropdowns.values():
        combo.set(TXT_SPECIAL_RULE_OPTION)
    app.transformations = {}

    targets = list(SCHEMAS["patienten"].keys())
    app.test_mapped_col = targets[0]
    app.test_rule_col = targets[1]

    app.mapping_dropdowns[app.test_mapped_col].set("id")
    app.on_column_mapped(app.test_mapped_col, "id")
    app.transformations[app.test_rule_col] = {"type": "static_value", "param": "x"}
    app.update_mapping_progress()
    app.apply_mapping_filter()
    return app


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

    def test_empty_preview_shows_placeholder(self, app):
        """Ohne Daten ist der Platzhalter sichtbar und die Paginierung deaktiviert."""
        app.source_df = None
        app.render_data_preview()
        app.render_source_columns_list()

        assert app.lbl_preview_empty.winfo_manager() == "place"
        assert app.lbl_preview_page_info.cget("text") == LBL_PREVIEW_PAGINATION_EMPTY
        assert app.btn_preview_prev.cget("state") == "disabled"
        assert app.btn_preview_next.cget("state") == "disabled"
        assert len(app.preview_tree.get_children()) == 0
        assert len(app.source_cols_scroll.winfo_children()) == 1

    def test_load_csv_updates_stats_and_preview(self, app, tmp_path):
        """Laden einer CSV füllt Statistiken, Vorschau und Quellspaltenliste."""
        csv_file = tmp_path / "patienten.csv"
        csv_file.write_text(
            "Vorname;Nachname;PLZ;IK\n"
            "Max;Mustermann;10115;123456789\n"
            "Erika;Schmidt;80331;987654321\n"
            "Hans;Meier;50667;112233445\n",
            encoding="utf-8",
        )

        with patch("pygrator.filedialog.askopenfilename", return_value=str(csv_file)):
            app.load_csv()

        assert app.lbl_stats_rows.cget("text") == LBL_STATS_ROWS_TEMPLATE.format(value=3)
        assert app.lbl_stats_cols.cget("text") == LBL_STATS_COLS_TEMPLATE.format(value=4)
        assert app.lbl_stats_sep.cget("text") == LBL_STATS_SEP_TEMPLATE.format(value="';'")
        assert app.lbl_preview_empty.winfo_manager() == ""
        assert list(app.preview_tree["columns"]) == ["Vorname", "Nachname", "PLZ", "IK"]
        assert len(app.preview_tree.get_children()) == 3
        assert app.lbl_preview_page_info.cget("text") == "1 - 3 / 3"
        assert len(app.source_cols_scroll.winfo_children()) == 4

    def test_preview_pagination(self, app):
        """Prüft Seitenwechsel und Seitengröße der Datenvorschau."""
        app.source_df = pd.DataFrame({
            "A": [f"val_a_{i}" for i in range(60)],
            "B": [f"val_b_{i}" for i in range(60)]
        })
        app.preview_page_size = 50
        app.preview_page = 0
        app.render_data_preview()

        # Seite 1: 50 Zeilen
        assert len(app.preview_tree.get_children()) == 50
        assert app.btn_preview_prev.cget("state") == "disabled"
        assert app.btn_preview_next.cget("state") == "normal"
        assert app.lbl_preview_page_info.cget("text") == "1 - 50 / 60"

        # Seite 2: 10 Zeilen
        app.on_preview_next_page()
        assert app.preview_page == 1
        assert len(app.preview_tree.get_children()) == 10
        assert app.btn_preview_prev.cget("state") == "normal"
        assert app.btn_preview_next.cget("state") == "disabled"
        assert app.lbl_preview_page_info.cget("text") == "51 - 60 / 60"

        # Über das Ende hinaus blättern bleibt auf der letzten Seite
        app.on_preview_next_page()
        assert app.preview_page == 1

        # Zurück zu Seite 1
        app.on_preview_prev_page()
        assert app.preview_page == 0
        assert len(app.preview_tree.get_children()) == 50

        # Seitengröße ändern auf 25 springt auf Seite 1
        app.on_preview_next_page()
        app.on_preview_size_change("25")
        assert app.preview_page == 0
        assert app.preview_page_size == 25
        assert len(app.preview_tree.get_children()) == 25
        assert app.lbl_preview_page_info.cget("text") == "1 - 25 / 60"

    def test_preview_renders_missing_values_as_empty(self, app):
        """Fehlende Werte erscheinen in der Vorschau leer statt als 'nan'/'None'."""
        app.source_df = pd.DataFrame({"A": ["x", None], "B": [None, "y"]})
        app.preview_page = 0
        app.render_data_preview()
        rows = [app.preview_tree.item(i, "values") for i in app.preview_tree.get_children()]
        assert [list(r) for r in rows] == [["x", ""], ["", "y"]]

    @pytest.mark.parametrize("mode, idx", [("Light", 0), ("Dark", 1)])
    def test_preview_colors_follow_appearance_mode(self, app, mode, idx):
        """Die Datenvorschau übernimmt die Farben des aktiven Light-/Dark-Mode."""
        with patch("pygrator.ctk.get_appearance_mode", return_value=mode):
            app._apply_treeview_colors()

        style = ttk.Style(app)
        assert style.lookup("Treeview", "background").lower() == COLOR_TREE_BG[idx].lower()
        assert str(app.preview_tree.tag_configure("odd", "background")).lower() == COLOR_TREE_ROW_ALT[idx].lower()

    def test_mapping_progress_calculation(self, mapped_app):
        """Zuordnung und Regel zählen jeweils als ein gemapptes Feld."""
        total = len(SCHEMAS["patienten"])
        expected_text = LBL_MAPPING_STATUS_TEMPLATE.format(mapped=2, total=total, percent=int(2 / total * 100))

        assert mapped_app.lbl_mapping_status.cget("text") == expected_text
        assert mapped_app.progress_mapping.get() == pytest.approx(2 / total, abs=0.01)

        # Regel entfernen -> nur noch ein Feld
        del mapped_app.transformations[mapped_app.test_rule_col]
        mapped_app.update_mapping_progress()
        assert mapped_app.progress_mapping.get() == pytest.approx(1 / total, abs=0.01)

    def test_status_filter_hides_rows(self, mapped_app):
        """Die Statusfilter blenden tatsächlich die passenden Zeilen ein bzw. aus."""
        all_cols = set(SCHEMAS["patienten"].keys())
        mapped_col = mapped_app.test_mapped_col
        rule_col = mapped_app.test_rule_col

        mapped_app.on_filter_change(LBL_FILTER_MAPPED)
        assert _visible_rows(mapped_app) == {mapped_col, rule_col}

        mapped_app.on_filter_change(LBL_FILTER_WITH_RULES)
        assert _visible_rows(mapped_app) == {rule_col}

        mapped_app.on_filter_change(LBL_FILTER_UNMAPPED)
        assert _visible_rows(mapped_app) == all_cols - {mapped_col, rule_col}

        mapped_app.on_filter_change(LBL_FILTER_ALL)
        assert _visible_rows(mapped_app) == all_cols

    def test_search_filters_rows(self, mapped_app):
        """Die Freitextsuche zeigt nur Zielspalten, die den Suchbegriff enthalten."""
        all_cols = set(SCHEMAS["patienten"].keys())
        query = "name"

        mapped_app.entry_search.delete(0, "end")
        mapped_app.entry_search.insert(0, query.upper())
        mapped_app.on_search_change()

        expected = {c for c in all_cols if query in c.lower()}
        assert expected, "Testvoraussetzung: Schema enthält Spalten mit 'name'"
        assert _visible_rows(mapped_app) == expected

        # Suche leeren -> alles wieder sichtbar
        mapped_app.entry_search.delete(0, "end")
        mapped_app.on_search_change()
        assert _visible_rows(mapped_app) == all_cols

    def test_rule_categories_metadata(self):
        """Verifiziert, dass alle wichtigen Regeln kategorisiert sind."""
        assert RULE_CATEGORIES["validate_ik"] == CAT_VALIDATION
        assert RULE_CATEGORIES["validate_kvnr"] == CAT_VALIDATION
        assert RULE_CATEGORIES["validate_email"] == CAT_VALIDATION
        assert RULE_CATEGORIES["format_date"] == CAT_FORMAT
        assert RULE_CATEGORIES["clean_plz"] == CAT_FORMAT
        assert RULE_CATEGORIES["gender"] == CAT_FORMAT
        assert RULE_CATEGORIES["clean_salutation"] == CAT_FORMAT
        assert RULE_CATEGORIES["split_street"] == CAT_SPLIT
        assert RULE_CATEGORIES["split_number"] == CAT_SPLIT
        assert RULE_CATEGORIES["generate_uid"] == CAT_GENERATE
        assert RULE_CATEGORIES["copy_target"] == CAT_GENERATE

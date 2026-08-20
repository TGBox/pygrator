from constants import COL_PURPLE
import os
import re
import csv
from typing import Any, Dict, List, Optional, Set, cast
from openpyxl import Workbook
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox

# DONE TODO: Check and verify that the newly added assignments for default connections between columns has worked as intended.
# DONE TODO: Add a way to automatically fill the insurance provider name from the ik number that is specified.
# DONE TODO: Add a way to add the name of a city from its post code and vice versa. There might be a method like this already in the py-handelsregister repositry! CHECK THAT OUT!
# DONE TODO: Add a verification for the IK number. (Only format [explicitly only numerical with length 9] or maybe with proper check of the IK?) => Last part maybe not feasible because these IKs are always private therapists and not commonly known institutions!
# DONE TODO: Add a verification for the insurance number. (one letter followed by 9 digits)
# DONE TODO: Add a way to map the left over fields to the additional fields, if the target is a patients table.
# DONE TODO: Add a method that can get turned on optionally in the gui. The method should list all field values that have been altered or that would be altered. Also with batch select and single select options on how to handle these entries.
# DONE TODO: Add rule for always copying the contents of "id" to "p_nr" or "ext_id" if these fields exist.
# DONE TODO: BUG: The completion rules for finding the city via the post code and for finding the post code via the city name are not selecting the correct reference column by default.
# DONE TODO: Add another dialog window, where a list with all elements gets shown, where the sanitize method will process the value. Then user selection single/batch for the operations that will get executed.
# DONE TODO: Add email structure validation.
# DONE TODO: Split this file into multiple parts.
# DONE TODO: Move all magic numbers, color values and other hard coded values to a dedicated file to have a single source of truth where changes can be applied more easily.
# DONE TODO: FEATURE: Add a check sum digit calculation for the IK as well.
# DONE TODO: FEATURE: The corrections for the insurance number must only get applied, when we can be sure, that our correction is useful. So we need to add an additional check to calculate the check sum digit at the end, after we applied our correction. And only if the result is viable, we want to change this value!
# DONE TODO: FEATURE: When a dataset export from another program already has a unique identifier for the individual elements, we want to transfer these values instead of just copying the rolf ID that was generated. (Also we may want to update the program in general, so that the p_nr will be a continuos counter that is easier for humans to reference.)
# DONE TODO: FEATURE: For doctors, we can just use the LANR (Lebenslange Arztnummer) to have unique identifiers. For other input sources, we need to check what their IDs are called.
    # TODO: The 2 todos above need to get verified with different source tables.
# TODO: FEATURE: Currently we only account for an empty database on our side. But the program should also be applicable when the database already has values and we get an updated table to update the individual data entries with the new information. Should only update certain fields where a change can be expected. (Maybe add a way to let the user decide, which fields need to adapt to the new source of truth and which will stay the same.)
# TODO: Rename the constants to better reflect their usage throughout the application. Also the names should apply to the elements which are being represented by them and not with the description of the current value. (So we currently have "COL_GREEN", but this could get renamed to "COL_BTN_FG" for example. So that a future change in the appearance of the app wouldn't result in a faulty descriptor for this constant!)
# TODO: Add validation for the values of the fields.
# TODO: Add more comments to this file.
# TODO: Add a way to implement input schemas for specific export types from different other software companies.
    # TODO: Add a way to add new schemas based on the currently processed input table.

from auto_complete import extract_title_and_clean_name, try_to_fix_insurance_number
from db_util import (
    format_date_iso, 
    generate_id, 
    parse_varchar_limit, 
    sanitize_data_string, 
    validate_ik_number, 
    validate_insurance_number, 
    validate_email, 
    extract_flagged_records
)
from schemas import SCHEMAS
from dialogs import center_window, ExtraFieldsDialog, RowValidationDialog, ValidationFixDialog, StringCleanupPreviewDialog
from constants import *


# Farbschema & Theme für modernere Optik
ctk.set_appearance_mode(APP_APPEARANCE_MODE)
ctk.set_default_color_theme(APP_COLOR_THEME)


class CSVMappingApp(ctk.CTk):
    source_df: Optional[pd.DataFrame]
    source_file_path: str
    transformations: Dict[str, Dict[str, Any]]
    mapping_dropdowns: Dict[str, ctk.CTkOptionMenu]
    trans_buttons: Dict[str, ctk.CTkButton]
    var_clean_strings: ctk.BooleanVar
    chk_fill_null: ctk.CTkCheckBox
    lbl_file: ctk.CTkLabel
    combo_schema: ctk.CTkOptionMenu
    combo_export_format: ctk.CTkOptionMenu
    combo_encoding: ctk.CTkOptionMenu
    scroll_frame: ctk.CTkScrollableFrame
    cleanup_dialog: Optional[StringCleanupPreviewDialog]
    ik_service: Any
    plz_service: Any
    _current_toast_frame: Optional[ctk.CTkFrame]
    _current_toast_timer: Optional[str]

    def __init__(self) -> None:
        super().__init__()

        self.title("CSV Data Mapper & Schema Validator")
        center_window(cast(ctk.CTkToplevel, cast(Any, self)), APP_WIDTH, APP_HEIGHT)
        
        # 1. Globale Autocomplete-Einstellungen initialisieren
        self.autocomplete_settings = {
            "split_title": True,       # Titel aus Name trennen
            "infer_gender": True,      # Geschlecht aus Vorname ableiten
            "infer_salutation": True,  # Anrede generieren
            "clean_kvnr": True         # KVNR bereinigen (O -> 0)
        }

        self.source_df = None
        self.source_file_path = ""
        self.transformations = {}  
        self.mapping_dropdowns = {}
        self.trans_buttons = {}
        self.cleanup_dialog = None
        self._current_toast_frame = None
        self._current_toast_timer = None
        
        self.var_clean_strings = ctk.BooleanVar(value=True)
        
        from services.ik_lookup import IKLookupService
        from services.plz_lookup import PLZLookupService
        
        self.ik_service = IKLookupService()
        self.plz_service = PLZLookupService()

        self._build_ui()

    def _build_ui(self) -> None:
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=PADDING_L, pady=PADDING_M)

        # Zeile 1: Aktionsleiste (Buttons & Schema-Auswahl)
        action_row = ctk.CTkFrame(top_frame, fg_color="transparent")
        action_row.pack(fill="x", padx=PADDING_M, pady=(PADDING_S, PADDING_XXS))

        ctk.CTkButton(action_row, text="Quelldatei laden (CSV)", command=self.load_csv).pack(side="left")

        self.btn_auto_settings = ctk.CTkButton(
            action_row,
            text="⚙️ Auto-Vervollständigung",
            command=self.open_autocomplete_settings_dialog
        )
        self.btn_auto_settings.pack(side="right", padx=(PADDING_M, 0))

        self.combo_schema = ctk.CTkOptionMenu(
            action_row, 
            values=list(SCHEMAS.keys()), 
            width=OPTIONS_MENU_WIDTH,
            command=self.on_schema_change
        )
        self.combo_schema.pack(side="right", padx=PADDING_XS)

        ctk.CTkLabel(action_row, text="Zielschema:").pack(side="right", padx=(PADDING_M, PADDING_XS))

        # Zeile 2: Datei-Informationen (vollständiger Dateiname & Details)
        info_row = ctk.CTkFrame(top_frame, fg_color="transparent")
        info_row.pack(fill="x", padx=PADDING_M, pady=(PADDING_XXS, PADDING_S))

        self.lbl_file = ctk.CTkLabel(info_row, text="Keine Datei ausgewählt", text_color="gray", anchor="w")
        self.lbl_file.pack(side="left", fill="x", expand=True)

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Spalten-Zuordnung & Schema-Limits")
        self.scroll_frame.pack(fill="both", expand=True, padx=PADDING_L, pady=PADDING_M)

        # UNTERE BEDIENLEISTE (EXPORT-OPTIONS)
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=PADDING_L, pady=PADDING_M)

        # Linker Bereich: Checkboxen
        chk_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        chk_frame.pack(side="left", padx=PADDING_M, pady=PADDING_XS)

        self.chk_fill_null = ctk.CTkCheckBox(
            chk_frame, 
            text="Unbelegte Felder mit 'NULL' auffüllen (statt leerem Text)"
        )
        self.chk_fill_null.pack(anchor="w", pady=PADDING_XXS)
        self.chk_fill_null.select()
        
        chk_clean_strings = ctk.CTkCheckBox(
            chk_frame, 
            text="String-Werte bereinigen (Trim & Steuerzeichen entfernen)",
            variable=self.var_clean_strings
        )
        chk_clean_strings.pack(side="left", pady=PADDING_XS)

        # Mittlerer Bereich: Format & Encoding Auswahlen
        export_opts_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        export_opts_frame.pack(side="left", padx=PADDING_XL, pady=PADDING_XS)

        # Format-Auswahl
        ctk.CTkLabel(export_opts_frame, text="Export-Format:", font=LABEL_FONT_BOLD).grid(row=0, column=0, sticky="w", padx=PADDING_XS)
        self.combo_export_format = ctk.CTkOptionMenu(
            export_opts_frame, 
            values=["CSV (Semikolon ';')", "CSV (Komma ',')", "Excel (.xlsx)"],
            width=OPTIONS_MENU_WIDTH,
            command=self.on_format_change
        )
        self.combo_export_format.grid(row=0, column=1, padx=PADDING_XS, pady=2)

        # Encoding-Auswahl
        ctk.CTkLabel(export_opts_frame, text="Encoding:", font=LABEL_FONT_BOLD).grid(row=1, column=0, sticky="w", padx=PADDING_XS)
        self.combo_encoding = ctk.CTkOptionMenu(
            export_opts_frame, 
            values=["utf-8-sig (Excel CSV)", "utf-8", "cp1252 (Windows)", "iso-8859-1"],
            width=OPTIONS_MENU_WIDTH
        )
        self.combo_encoding.grid(row=1, column=1, padx=PADDING_XS, pady=2)

        # Rechter Bereich: Buttons für Inspektion und Export
        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=PADDING_M, pady=PADDING_M)

        ctk.CTkButton(
            btn_frame, 
            text="⚠️ Nur Abweichungen prüfen",
            text_color=COL_WHITE,
            fg_color=COL_ORANGE,
            hover_color=COL_DARK_ORANGE,
            font=BUTTON_FONT,
            width=PROCESS_BUTTON_WIDTH,
            command=self.run_pre_check_export
        ).pack(anchor="w", padx=(0, PADDING_S), pady=(0, PADDING_S), side="top")

        ctk.CTkButton(
            btn_frame, 
            text="Prüfen & Exportieren", 
            text_color=COL_WHITE,
            fg_color=COL_GREEN, 
            hover_color=COL_DARK_GREEN,
            font=BUTTON_FONT,
            width=PROCESS_BUTTON_WIDTH,
            command=self.start_processing
        ).pack(anchor="w", padx=(0, PADDING_S), pady=(0, PADDING_S), side="top")
        
    def open_autocomplete_settings_dialog(self):
        """Öffnet das Einstellungsfenster für die automatische Vervollständigung"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Einstellungen: Automatische Vervollständigung")

        ctk.CTkLabel(
            dialog, 
            text="Welche Regeln sollen beim Import angewendet werden?", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        vars_dict = {}
        options = [
            ("split_title", "🎓 Titel von Namen trennen (z. B. Dr. med.)"),
            ("infer_gender", "⚥ Geschlecht anhand des Vornamens ermitteln"),
            ("infer_salutation", "✉️ Anrede (Herr/Frau) automatisch ergänzen"),
            ("clean_kvnr", "🆔 KVNR bereinigen ('O' -> '0')")
        ]

        for key, label_text in options:
            var = ctk.BooleanVar(value=self.autocomplete_settings[key])
            chk = ctk.CTkCheckBox(dialog, text=label_text, variable=var)
            chk.pack(anchor="w", padx=25, pady=8)
            vars_dict[key] = var

        def save_and_close():
            for key in vars_dict:
                self.autocomplete_settings[key] = vars_dict[key].get()
            dialog.destroy()

        btn_save = ctk.CTkButton(dialog, text="Übernehmen", command=save_and_close)
        btn_save.pack(pady=(20, 0))

        center_window(dialog, AUTO_COMPLETE_DIALOG_WIDTH, AUTO_COMPLETE_DIALOG_HEIGHT)
        dialog.grab_set()  # Fenster modal machen (Vordergrund erzwingen)

    def on_format_change(self, choice: str) -> None:
        """Aktiviert/Deaktiviert das Encoding-Dropdown je nach Format."""
        if "Excel" in choice:
            self.combo_encoding.configure(state="disabled")
        else:
            self.combo_encoding.configure(state="normal")
    
    def load_csv(self) -> None:
        file_path: str = filedialog.askopenfilename(filetypes=[("CSV/Excel Files", "*.csv;*.txt;*.xlsx;*.xls")])
        if not file_path:
            return

        ext: str = os.path.splitext(file_path)[1].lower()
        loaded_df: Optional[pd.DataFrame] = None
        used_encoding: str = "Binary"
        detected_sep: str = "N/A"

        if ext in ['.xlsx', '.xls']:
            try:
                raw_excel: pd.DataFrame = pd.read_excel(file_path, dtype=str) # type: ignore
                loaded_df = pd.DataFrame(raw_excel)
            except Exception as e:
                messagebox.showerror("Fehler beim Laden", f"Konnte Excel-Datei nicht lesen:\n{str(e)}")
                return
        else:
            detected_sep = ';'
            try:
                with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    sample: str = f.read(MAX_CHAR_READ)
                    sniffer: csv.Sniffer = csv.Sniffer()
                    detected_sep = sniffer.sniff(sample).delimiter
            except Exception:
                pass

            encodings_to_try: List[str] = ['utf-8-sig', 'utf-8', 'cp1252', 'latin1']
            for enc in encodings_to_try:
                try:
                    raw_csv = pd.read_csv(
                        file_path, 
                        sep=detected_sep, 
                        encoding=enc, 
                        on_bad_lines='skip',
                        dtype=str
                    )
                    loaded_df = raw_csv
                    used_encoding = enc
                    break
                except Exception:
                    continue

        if loaded_df is not None:
            self.source_df = loaded_df
            self.source_file_path = file_path
            cast(Any, self.lbl_file).configure(
                text=f"📁 Datei: {os.path.basename(file_path)}  |  Trennzeichen: '{detected_sep}'  |  Encoding: {used_encoding}", 
                text_color=COL_WHITE
            )
            self.render_mapping_rows()
        else:
            messagebox.showerror("Fehler beim Laden", "Konnte die Datei nicht lesen.")

    def on_schema_change(self, choice: str) -> None:
        if self.source_df is not None:
            self.render_mapping_rows()

    def render_mapping_rows(self) -> None:
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if self.source_df is None:
            return

        source_cols: List[str] = ["-- Nicht zuordnen / Spezielle Regel --"] + list(self.source_df.columns)
        target_schema: Dict[str, str] = SCHEMAS[self.combo_schema.get()]

        ctk.CTkLabel(self.scroll_frame, text="Zielspalte (Datentyp)", font=BUTTON_FONT).grid(row=0, column=0, padx=PADDING_M, pady=PADDING_XS, sticky="w")
        ctk.CTkLabel(self.scroll_frame, text="Quellspalte (CSV)", font=BUTTON_FONT).grid(row=0, column=1, padx=PADDING_M, pady=PADDING_XS, sticky="w")
        ctk.CTkLabel(self.scroll_frame, text="Spezielle Transformation", font=BUTTON_FONT).grid(row=0, column=2, padx=PADDING_M, pady=PADDING_XS, sticky="w")

        self.mapping_dropdowns = {}
        self.trans_buttons = {}

        source_id_col = next((str(c) for c in self.source_df.columns if str(c).lower() in ["id", "patient_id", "patienten_id", "pat_id"]), None)
        source_lanr_col = next((str(c) for c in self.source_df.columns if str(c).lower() in ["LANR", "lanr", "la-nr", "la_nr"]), None)

        for idx, (target_col, dtype) in enumerate(target_schema.items(), start=1):
            label_text: str = f"{target_col} ({dtype})"
            ctk.CTkLabel(self.scroll_frame, text=label_text, font=SMALL_LABEL_FONT).grid(row=idx, column=0, padx=PADDING_M, pady=PADDING_XS, sticky="w")

            combo: ctk.CTkOptionMenu = ctk.CTkOptionMenu(self.scroll_frame, values=source_cols)
            combo.grid(row=idx, column=1, padx=PADDING_M, pady=PADDING_XS, sticky="w")
            
            target_lower: str = target_col.lower()
            
            for src_col in self.source_df.columns:
                src_lower: str = str(src_col).lower()

                if src_lower == target_lower:
                    combo.set(str(src_col))
                    break

                if target_lower in ["telefonmobil", "mobil", "p_handy"]:
                    if src_lower in ["mobil", "handy", "mobile", "telefonmobil"]:
                        combo.set(str(src_col))
                        break
                    continue

                if target_lower in ["telefon", "p_tel", "tel"]:
                    if src_lower in ["telefon", "p_tel", "tel", "telefon1"]:
                        combo.set(str(src_col))
                        break

                if src_lower == "titel" and "name1" in target_lower:
                    combo.set(str(src_col))
                    break
                if src_lower == "vorname" and ("name2" in target_lower or "p_vname" in target_lower):
                    combo.set(str(src_col))
                    break
                if src_lower == "nachname" and ("name3" in target_lower or "p_name" in target_lower):
                    combo.set(str(src_col))
                    break

                if src_lower == "wohnort" and "p_ort" in target_lower:
                    combo.set(str(src_col))
                    break
                if src_lower == "geburtsdatum" and "p_birth" in target_lower:
                    combo.set(str(src_col))
                    break
                if src_lower == "geschlecht" and any(k in target_lower for k in ["anrede", "p_anrede"]):
                    combo.set(str(src_col))
                    break
                if src_lower == "telefon2" and "p_telge" in target_lower:
                    combo.set(str(src_col))
                    break
                if src_lower in ("strasse", "straße") and any(k in target_lower for k in ["p_street", "p_hausnummer", "strasse", "straße"]):
                    combo.set(str(src_col))
                    break
                if src_lower == "kas_ik" and "p_ik" in target_lower:
                    combo.set(str(src_col))
                    break
                if src_lower == "status" and "p_vs" in target_lower:
                    combo.set(str(src_col))
                    break
                if src_lower == "versichertennummer" and "p_vnr" in target_lower:
                    combo.set(str(src_col))
                    break

                if (src_lower in target_lower or target_lower in src_lower) and len(src_lower) > 3:
                    combo.set(str(src_col))
                    break

            self.mapping_dropdowns[target_col] = combo

            if target_col not in self.transformations:
                if target_col == "id":
                    self.transformations[target_col] = {'type': 'generate_uid'}
                elif target_col == "p_nr":
                    if source_id_col:
                        combo.set(source_id_col)
                        self.transformations[target_col] = {'type': 'none'}
                    else:
                        self.transformations[target_col] = {'type': 'auto_sequence_6'}
                elif target_col == "ext_id":
                    if source_id_col:
                        combo.set(source_id_col)
                        self.transformations[target_col] = {'type': 'none'}
                    elif source_lanr_col:
                        combo.set(source_lanr_col)
                        self.transformations[target_col] = {'type': 'none'}
                    else:
                        self.transformations[target_col] = {'type': 'auto_sequence_6'}
                elif "birth" in target_col:
                    self.transformations[target_col] = {'type': 'format_date'}
                elif "anrede" in target_col:
                    self.transformations[target_col] = {'type': 'gender'}
                elif "plz" in target_col:
                    city_col: Optional[str] = next((str(c) for c in self.source_df.columns if str(c).lower() in ["ort", "wohnort", "stadt"]), None)
                    if city_col:
                        self.transformations[target_col] = {'type': 'lookup_plz_by_city', 'param': city_col}
                    else:
                        self.transformations[target_col] = {'type': 'clean_plz'}
                elif target_col in ("p_ort", "ort"):
                    plz_col: Optional[str] = next((str(c) for c in self.source_df.columns if "plz" in str(c).lower()), None)
                    if plz_col:
                        self.transformations[target_col] = {'type': 'lookup_city_by_plz', 'param': plz_col}
                elif "street" in target_col:
                    self.transformations[target_col] = {'type': 'split_street'}
                elif "hausnummer" in target_col:
                    self.transformations[target_col] = {'type': 'split_number'}
                elif target_col == "p_krankenkasse":
                    for src_col in self.source_df.columns:
                        if "ik" in str(src_col).lower():
                            self.transformations[target_col] = {
                                'type': 'lookup_ik_provider',
                                'param': str(src_col)
                            }
                            break
                elif target_col in ("p_ik", "ik") or "ik_nummer" in target_col:
                    self.transformations[target_col] = {'type': 'validate_ik'}
                elif target_col in ("p_vnr", "vnr", "kvnr") or "versichertennummer" in target_col:
                    self.transformations[target_col] = {'type': 'validate_kvnr'}
                elif target_col in ("p_email", "email", "mail", "Email", "E-Mail"):
                    self.transformations[target_col] = {'type': 'validate_email'}

            btn_trans: ctk.CTkButton = ctk.CTkButton(
                self.scroll_frame, 
                text="Regel hinzufügen...", 
                width=RULE_BUTTON_WIDTH,
                fg_color=COL_GRAY_30,
                command=lambda t=target_col: self.open_transformation_dialog(t)
            )
            btn_trans.grid(row=idx, column=2, padx=PADDING_M, pady=PADDING_XS, sticky="w")
            self.trans_buttons[target_col] = btn_trans

            # Rechtsklick-Event zum direkten Entfernen/Deselektieren der Regel binden
            def _make_right_click_handler(col: str) -> Any:
                def _handler(event: Any) -> str:
                    self.remove_rule_direct(col)
                    return "break"
                return _handler

            handler = _make_right_click_handler(target_col)
            btn_trans.bind("<Button-3>", handler)
            btn_trans.bind("<Button-2>", handler)
            if hasattr(btn_trans, "_canvas") and btn_trans._canvas:
                btn_trans._canvas.bind("<Button-3>", handler)
                btn_trans._canvas.bind("<Button-2>", handler)
            if hasattr(btn_trans, "_text_label") and btn_trans._text_label:
                btn_trans._text_label.bind("<Button-3>", handler)
                btn_trans._text_label.bind("<Button-2>", handler)

        self.update_all_rule_button_states()

    def show_toast(self, message: str, duration_ms: int = 2500, icon: str = "ℹ️") -> None:
        """Zeigt eine elegante, nicht-modale In-App Toast-Benachrichtigung am unteren Rand an."""
        if hasattr(self, "_current_toast_frame") and self._current_toast_frame:
            try:
                if hasattr(self, "_current_toast_timer") and self._current_toast_timer:
                    self.after_cancel(self._current_toast_timer)
                self._current_toast_frame.destroy()
            except Exception:
                pass

        toast_frame = ctk.CTkFrame(
            self,
            fg_color=COL_PURPLE,
            border_color=COL_DARK_GREEN,
            border_width=1,
            corner_radius=12
        )
        toast_frame.place(relx=0.5, rely=0.92, anchor="center")

        label = ctk.CTkLabel(
            toast_frame,
            text=f"{icon}  {message}",
            font=BUTTON_FONT,
            text_color=COL_WHITE,
            padx=PADDING_L,
            pady=PADDING_S
        )
        label.pack()

        self._current_toast_frame = toast_frame

        def dismiss() -> None:
            try:
                if hasattr(self, "_current_toast_frame") and self._current_toast_frame == toast_frame:
                    toast_frame.destroy()
                    self._current_toast_frame = None
            except Exception:
                pass

        self._current_toast_timer = self.after(duration_ms, dismiss)

    def remove_rule_direct(self, target_col: str) -> None:
        """Entfernt eine Regel direkt per Rechtsklick ohne Bestätigungsdialog."""
        if target_col in self.transformations and self.transformations[target_col].get('type') != 'none':
            rule_info = self.transformations[target_col]
            rule_type = rule_info.get('type', '')
            rule_title = RULE_NAMES.get(rule_type, rule_type)
            del self.transformations[target_col]
            self.update_rule_button_state(target_col)
            self.show_toast(f"Regel '{rule_title}' für '{target_col}' entfernt", icon="🗑️")
        else:
            self.show_toast(f"Keine Regel für '{target_col}' vorhanden", icon="ℹ️")
            
    def update_all_rule_button_states(self) -> None:
        if hasattr(self, 'trans_buttons'):
            for target_col in self.trans_buttons.keys():
                self.update_rule_button_state(target_col)
            
    def update_rule_button_state(self, target_col: str) -> None:
        btn: Optional[ctk.CTkButton] = self.trans_buttons.get(target_col)
        if not btn:
            return

        rule: Dict[str, Any] = self.transformations.get(target_col, {})
        rule_type: Optional[str] = rule.get('type') if rule else None
        param: Optional[Any] = rule.get('param') if rule else None

        if rule_type and rule_type != "none":
            rule_title: str = RULE_NAMES.get(rule_type, rule_type)
            button_text: str = f"✓ {rule_title} (\"{param}\")" if param else f"✓ {rule_title}"

            cast(Any, btn).configure(
                text=button_text,
                fg_color=COL_DARK_GREEN,
                hover_color=COL_DARKER_GREEN
            )
        else:
            cast(Any, btn).configure(
                text="Regel hinzufügen...",
                fg_color=COL_GRAY_30,
                hover_color=COL_GRAY_40
            )

    def open_transformation_dialog(self, target_col: str) -> None:
        target_schema: Dict[str, str] = SCHEMAS[self.combo_schema.get()]
        other_target_cols: List[str] = [col for col in target_schema.keys() if col != target_col]

        dialog: ctk.CTkToplevel = ctk.CTkToplevel(self)
        dialog.title(f"Transformation für '{target_col}'")
        center_window(dialog, TRANSFORMATION_DIALOG_WIDTH, TRANSFORMATION_DIALOG_HEIGHT)
        dialog.grab_set()

        # 1. Header (Oben fixiert)
        ctk.CTkLabel(dialog, text=f"Regel definieren für: '{target_col}'", font=BUTTON_FONT).pack(pady=PADDING_S)

        # 2. Fußzeile für Aktions-Buttons (Unten fixiert, bleibt IMMER sichtbar!)
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=PADDING_M)

        # 3. Mittlerer scrollbarer Inhaltsbereich
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(fill="both", expand=True, padx=PADDING_M, pady=PADDING_XS)

        existing_rule: Dict[str, Any] = self.transformations.get(target_col, {})
        
        default_rule: str = 'none'
        if target_col == 'p_nr':
            default_rule = 'auto_sequence_6'
        elif 'plz' in target_col.lower():
            default_rule = 'clean_plz'
        elif target_col == 'id':
            default_rule = 'generate_uid'
        elif 'birth' in target_col.lower() or 'datum' in target_col.lower() or target_col.endswith('_bis'):
            default_rule = 'format_date'
        elif 'anrede' in target_col.lower():
            default_rule = 'gender'
        elif 'hausnummer' in target_col.lower():
            default_rule = 'split_number'
        elif 'street' in target_col.lower():
            default_rule = 'split_street'
        elif 'p_nr' in target_col.lower():
            default_rule = 'split_number'
        elif 'mail' in target_col.lower():
            default_rule = 'validate_email'

        current_type: str = str(existing_rule.get('type', default_rule))
        rule_type: ctk.StringVar = ctk.StringVar(value=current_type)

        r0 = ctk.CTkRadioButton(scroll_frame, text="🔑 Neue UID generieren (Kompakt)", variable=rule_type, value="generate_uid")
        r0.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        r_copy = ctk.CTkRadioButton(scroll_frame, text="🔗 Wert aus anderer Zielspalte übernehmen", variable=rule_type, value="copy_target")
        r_copy.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        copy_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        copy_frame.pack(anchor="w", padx=PADDING_XXXL, pady=2)
        ctk.CTkLabel(copy_frame, text="Kopieren aus:").pack(side="left", padx=PADDING_XS)
        combo_copy_target = ctk.CTkOptionMenu(copy_frame, values=other_target_cols if other_target_cols else ["Keine"])
        combo_copy_target.pack(side="left")
        if existing_rule.get('type') == 'copy_target' and str(existing_rule.get('param')) in other_target_cols:
            combo_copy_target.set(str(existing_rule.get('param')))

        r_date = ctk.CTkRadioButton(scroll_frame, text="📅 Datumsformat anpassen -> YYYY-MM-DD", variable=rule_type, value="format_date")
        r_date.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        date_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        date_frame.pack(anchor="w", padx=PADDING_XXXL, pady=2)
        ctk.CTkLabel(date_frame, text="Standardwert bei leeren Feldern (optional):", font=SMALL_LABEL_FONT, text_color=COL_GRAY_70).pack(side="left", padx=PADDING_XS)
        entry_date_default = ctk.CTkEntry(date_frame, width=OPTIONS_MENU_WIDTH, placeholder_text="z. B. 1900-01-01")
        entry_date_default.pack(side="left")
        if existing_rule.get('type') == 'format_date' and existing_rule.get('param'):
            entry_date_default.insert(0, str(existing_rule.get('param')))
        
        separator = ctk.CTkFrame(scroll_frame, height=2, fg_color=COL_GRAY_30)
        separator.pack(fill="x", padx=PADDING_XL, pady=PADDING_M)

        r_default = ctk.CTkRadioButton(scroll_frame, text="✨ Standardwert nur für LEERE Felder setzen", variable=rule_type, value="default_value")
        r_default.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        default_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        default_frame.pack(anchor="w", padx=PADDING_XXXL, pady=2)
        ctk.CTkLabel(default_frame, text="Ersatzwert:").pack(side="left", padx=PADDING_XS)
        entry_default_val = ctk.CTkEntry(default_frame, width=VALUE_FIELD_WIDTH, placeholder_text="z. B. Unbekannt")
        entry_default_val.pack(side="left")
        if existing_rule.get('type') == 'default_value':
            entry_default_val.insert(0, str(existing_rule.get('param', '')))

        r_static = ctk.CTkRadioButton(scroll_frame, text="📌 Statischen Festwert für ALLE Zeilen setzen", variable=rule_type, value="static_value")
        r_static.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        static_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        static_frame.pack(anchor="w", padx=PADDING_XXXL, pady=2)
        ctk.CTkLabel(static_frame, text="Wert:").pack(side="left", padx=PADDING_XS)
        entry_static_val = ctk.CTkEntry(static_frame, width=VALUE_FIELD_WIDTH)
        entry_static_val.pack(side="left")
        if existing_rule.get('type') == 'static_value':
            entry_static_val.insert(0, str(existing_rule.get('param', '')))

        separator2 = ctk.CTkFrame(scroll_frame, height=2, fg_color=COL_GRAY_30)
        separator2.pack(fill="x", padx=PADDING_XL, pady=PADDING_M)
        
        r_ik_lookup = ctk.CTkRadioButton(
            scroll_frame, 
            text="🏢 Krankenkassenname aus IK-Quellspalte ermitteln", 
            variable=rule_type, 
            value="lookup_ik_provider"
        )
        r_ik_lookup.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        ik_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        ik_frame.pack(anchor="w", padx=PADDING_XXXL, pady=2)
        ctk.CTkLabel(ik_frame, text="IK-Quellspalte:").pack(side="left", padx=PADDING_XS)

        source_cols_list: List[str] = [str(c) for c in self.source_df.columns] if self.source_df is not None else []
        combo_ik_source = ctk.CTkOptionMenu(ik_frame, values=source_cols_list if source_cols_list else ["Keine"])
        combo_ik_source.pack(side="left")

        if existing_rule.get('type') == 'lookup_ik_provider' and str(existing_rule.get('param')) in source_cols_list:
            combo_ik_source.set(str(existing_rule.get('param')))
        elif self.source_df is not None:
            for c in source_cols_list:
                if 'ik' in c.lower():
                    combo_ik_source.set(c)
                    break
                
        r_val_ik = ctk.CTkRadioButton(
            scroll_frame, 
            text="✔️ IK-Nummer auf Gültigkeit prüfen (Prüfziffer)", 
            variable=rule_type, 
            value="validate_ik"
        )
        r_val_ik.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        r_val_kvnr = ctk.CTkRadioButton(
            scroll_frame, 
            text="✔️ Krankenversichertennummer (KVNR) auf Gültigkeit prüfen", 
            variable=rule_type, 
            value="validate_kvnr"
        )
        r_val_kvnr.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        r_val_mail = ctk.CTkRadioButton(
            scroll_frame, 
            text="✔️ E-Mailadresse auf Gültigkeit prüfen", 
            variable=rule_type, 
            value="validate_email"
        )
        r_val_mail.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        r_plz = ctk.CTkRadioButton(scroll_frame, text="📮 PLZ bereinigen (.0 entfernen & 5 Stellen)", variable=rule_type, value="clean_plz")
        r_plz.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        r_seq = ctk.CTkRadioButton(
            scroll_frame, 
            text="🔢 Lineare Nummerierung (6-stellig, z. B. 000001)", 
            variable=rule_type, 
            value="auto_sequence_6"
        )
        r_seq.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        r_plz_lookup = ctk.CTkRadioButton(
            scroll_frame, 
            text="📮 PLZ basierend auf Ortsname-Quellspalte ergänzen", 
            variable=rule_type, 
            value="lookup_plz_by_city"
        )
        r_plz_lookup.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        plz_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        plz_frame.pack(anchor="w", padx=PADDING_XXXL, pady=2)
        ctk.CTkLabel(plz_frame, text="Ortsname-Quellspalte:").pack(side="left", padx=PADDING_XS)
        combo_city_source = ctk.CTkOptionMenu(plz_frame, values=source_cols_list if source_cols_list else ["Keine"])
        combo_city_source.pack(side="left")

        if existing_rule.get('type') == 'lookup_plz_by_city' and str(existing_rule.get('param')) in source_cols_list:
            combo_city_source.set(str(existing_rule.get('param')))
        elif self.source_df is not None:
            for c in source_cols_list:
                if c.lower() in ["ort", "wohnort", "stadt"]:
                    combo_city_source.set(c)
                    break

        r_city_lookup = ctk.CTkRadioButton(
            scroll_frame, 
            text="🏙️ Ort basierend auf PLZ-Quellspalte ergänzen", 
            variable=rule_type, 
            value="lookup_city_by_plz"
        )
        r_city_lookup.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        city_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        city_frame.pack(anchor="w", padx=PADDING_XXXL, pady=2)
        ctk.CTkLabel(city_frame, text="PLZ-Quellspalte:").pack(side="left", padx=PADDING_XS)
        combo_plz_source = ctk.CTkOptionMenu(city_frame, values=source_cols_list if source_cols_list else ["Keine"])
        combo_plz_source.pack(side="left")

        if existing_rule.get('type') == 'lookup_city_by_plz' and str(existing_rule.get('param')) in source_cols_list:
            combo_plz_source.set(str(existing_rule.get('param')))
        elif self.source_df is not None:
            for c in source_cols_list:
                if "plz" in c.lower():
                    combo_plz_source.set(c)
                    break

        r1 = ctk.CTkRadioButton(scroll_frame, text="👫 Geschlecht mappen (M->Herr, W->Frau)", variable=rule_type, value="gender")
        r1.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        separator3 = ctk.CTkFrame(scroll_frame, height=2, fg_color=COL_GRAY_30)
        separator3.pack(fill="x", padx=PADDING_XL, pady=PADDING_M)

        r2 = ctk.CTkRadioButton(scroll_frame, text="🏠 Straße/(Hausnr.) trennen -> Nur Straßenname", variable=rule_type, value="split_street")
        r2.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        r3 = ctk.CTkRadioButton(scroll_frame, text="🔢 (Straße)/Hausnr. trennen -> Nur Hausnummer", variable=rule_type, value="split_number")
        r3.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        r_merge = ctk.CTkRadioButton(scroll_frame, text="🔗 Zwei Quellspalten zusammenführen (mit Leerzeichen)", variable=rule_type, value="merge_columns")
        r_merge.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        merge_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        merge_frame.pack(anchor="w", padx=PADDING_XXXL, pady=2)
        ctk.CTkLabel(merge_frame, text="Zweite Quellspalte:").pack(side="left", padx=PADDING_XS)

        combo_merge_source = ctk.CTkOptionMenu(merge_frame, values=source_cols_list if source_cols_list else ["Keine"])
        combo_merge_source.pack(side="left")

        if existing_rule.get('type') == 'merge_columns' and str(existing_rule.get('param')) in source_cols_list:
            combo_merge_source.set(str(existing_rule.get('param')))

        def save_rule() -> None:
            t_type: str = rule_type.get()
            param: Optional[str] = None

            if t_type == "copy_target":
                param = combo_copy_target.get()
            elif t_type == "lookup_plz_by_city":
                param = combo_city_source.get()
            elif t_type == "lookup_city_by_plz":
                param = combo_plz_source.get()
            elif t_type == "lookup_ik_provider":
                param = combo_ik_source.get()
            elif t_type == "static_value":
                param = entry_static_val.get()
            elif t_type == "default_value":
                param = entry_default_val.get()
            elif t_type == "format_date":
                param = entry_date_default.get().strip()

            self.transformations[target_col] = {
                'type': t_type,
                'param': param
            }
            self.update_rule_button_state(target_col)
            rule_title: str = RULE_NAMES.get(t_type, t_type)
            self.show_toast(f"Regel '{rule_title}' für '{target_col}' hinterlegt.", icon="✓")
            dialog.destroy()

        def remove_rule() -> None:
            if target_col in self.transformations:
                del self.transformations[target_col]
            self.update_rule_button_state(target_col)
            self.show_toast(f"Keine Regel mehr für '{target_col}' aktiv.", icon="🗑️")
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="Speichern", command=save_rule).pack(side="left", expand=True, padx=PADDING_S)
        ctk.CTkButton(btn_frame, text="Regel löschen", fg_color="red3", hover_color="red4", command=remove_rule).pack(side="left", expand=True, padx=PADDING_S)

    def start_processing(self) -> None:
        """Startet den Gesamtablauf: Prüft Vorschaudialog und führt danach den Export aus."""
        if self.source_df is None:
            messagebox.showerror("Fehler", "Keine Datei geladen!")
            return

        assert self.source_df is not None

        active_source_cols: Set[str] = set()
        
        if hasattr(self, 'mapping_dropdowns'):
            for combo in self.mapping_dropdowns.values():
                src_col: str = combo.get()
                if src_col and src_col != "-- Nicht zuordnen / Spezielle Regel --" and src_col in self.source_df.columns:
                    active_source_cols.add(src_col)

        for rule in self.transformations.values():
            if rule.get('param'):
                p_col: str = str(rule['param'])
                if p_col in self.source_df.columns:
                    active_source_cols.add(p_col)

        if not active_source_cols:
            self.process_and_export()
            return

        if hasattr(self, 'var_clean_strings') and self.var_clean_strings.get():
            preview_items: List[Dict[str, Any]] = []
            
            for col in active_source_cols:
                for idx, original_val in self.source_df[col].items():
                    if pd.isna(original_val):
                        continue
                    
                    orig_str: str = str(original_val)
                    if not orig_str.strip():
                        continue

                    cleaned_val: str = sanitize_data_string(orig_str, remove_special_chars=True)
                    
                    if cleaned_val != orig_str:
                        preview_items.append({
                            'row_idx': idx,
                            'col_name': col,
                            'original': orig_str,
                            'cleaned': cleaned_val
                        })
            
            if preview_items:
                self.cleanup_dialog = StringCleanupPreviewDialog(self, preview_items)
                self.wait_window(self.cleanup_dialog)
                
                accepted_changes: Optional[List[Dict[str, Any]]] = self.cleanup_dialog.result
                
                if accepted_changes is None:
                    return
                
                for change in accepted_changes:
                    r: Any = change['row_idx']
                    c: str = str(change['col_name'])
                    self.source_df.at[r, c] = change['cleaned']

        self.process_and_export()

    def process_and_export(self) -> None:
        if self.source_df is None:
            messagebox.showerror("Fehler", "Keine Datei geladen!")
            return

        assert self.source_df is not None

        out_df: pd.DataFrame = pd.DataFrame()
        mapped_source_cols: Set[str] = set()
        row_count: int = len(self.source_df)

        target_schema: Dict[str, str] = SCHEMAS[self.combo_schema.get()]
        default_empty_value: str = "NULL" if self.chk_fill_null.get() else ""

        copy_rules: Dict[str, str] = {}
        invalid_records: List[Dict[str, Any]] = []
        
        if not hasattr(self, 'plz_service'):
            from services.plz_lookup import PLZLookupService
            self.plz_service = PLZLookupService()
            
        # =========================================================================
        # NEU: PRE-PROCESSING / AUTO-VERVOLLSTÄNDIGUNG (basierend auf Settings)
        # =========================================================================
        if hasattr(self, 'autocomplete_settings'):
            # 1. Title Split & Name Cleaning
            if self.autocomplete_settings.get("split_title"):
                for target_col, dropdown in self.mapping_dropdowns.items():
                    if 'nachname' in target_col.lower() or 'name' in target_col.lower():
                        src_c = dropdown.get()
                        if src_c and src_c in self.source_df.columns:
                            # Wendet extract_title_and_clean_name auf die Quell-Spalte an
                            res = self.source_df[src_c].astype(str).apply(extract_title_and_clean_name)
                            # Wenn eine eigene Titel-Spalte existiert, befüllen wir sie mit dem extrahierten Titel
                            if 'titel' in self.mapping_dropdowns:
                                out_df['titel'] = [t[0] for t in res]
                            self.source_df[src_c] = [t[1] for t in res]

            # 2. KVNR-Bereinigung ('O' -> '0') vor der Validierung
            if self.autocomplete_settings.get("clean_kvnr"):
                for target_col, dropdown in self.mapping_dropdowns.items():
                    if 'kvnr' in target_col.lower() or 'versichertennummer' in target_col.lower():
                        src_c = dropdown.get()
                        if src_c and src_c in self.source_df.columns:
                            self.source_df[src_c] = self.source_df[src_c].astype(str).str.upper().str.replace("O", "0")

        # PASS 1: Transformationen ausführen
        for target_col, _ in target_schema.items():
            rule: Dict[str, Any] = self.transformations.get(target_col, {})
            rule_type: Optional[str] = rule.get('type') if rule else None
            param: Optional[Any] = rule.get('param') if rule else None
            source_col: Optional[str] = self.mapping_dropdowns[target_col].get() if target_col in self.mapping_dropdowns else None

            if rule_type == "validate_ik":
                if source_col and source_col in self.source_df.columns:
                    for row_idx, val in self.source_df[source_col].items():
                        if pd.notna(val) and str(val).strip():
                            cleaned_ik: str = str(val).strip().split('.')[0].zfill(9)
                            if not validate_ik_number(cleaned_ik):
                                invalid_records.append({
                                    'row_idx': row_idx,
                                    'target_col': target_col,
                                    'rule_type': rule_type,
                                    'original_val': str(val),
                                    'action': 'keep',
                                    'custom_val': ''
                                })
                    out_df[target_col] = self.source_df[source_col]
                else:
                    out_df[target_col] = default_empty_value

            elif rule_type == "validate_kvnr":
                if source_col and source_col in self.source_df.columns:
                    out_df[target_col] = self.source_df[source_col].copy()

                    for row_idx, val in self.source_df[source_col].items():
                        if pd.notna(val) and str(val).strip():
                            cleaned_kvnr: str = str(val).strip().upper()

                            is_fixed: bool
                            fixed_kvnr: str
                            is_fixed, fixed_kvnr = try_to_fix_insurance_number(cleaned_kvnr)

                            if is_fixed:
                                out_df.at[row_idx, target_col] = fixed_kvnr

                            if not validate_insurance_number(fixed_kvnr):
                                invalid_records.append({
                                    'row_idx': row_idx,
                                    'target_col': target_col,
                                    'rule_type': rule_type,
                                    'original_val': str(val),
                                    'action': 'keep',
                                    'custom_val': ''
                                })
                else:
                    out_df[target_col] = default_empty_value
                    
            elif rule_type == "validate_email":
                if source_col and source_col in self.source_df.columns:
                    for row_idx, val in self.source_df[source_col].items():
                        if pd.notna(val) and str(val).strip():
                            cleaned_email: str = str(val).strip()
                            if not validate_email(cleaned_email):
                                invalid_records.append({
                                    'row_idx': row_idx,
                                    'target_col': target_col,
                                    'rule_type': rule_type,
                                    'original_val': str(val),
                                    'action': 'keep',
                                    'custom_val': ''
                                })
                    out_df[target_col] = self.source_df[source_col]
                else:
                    out_df[target_col] = default_empty_value

            if not rule_type:
                if 'birth' in target_col.lower() or 'datum' in target_col.lower() or target_col.endswith('_bis'):
                    rule_type = 'format_date'
                elif 'plz' in target_col.lower():
                    rule_type = 'clean_plz'
                elif 'anrede' in target_col.lower():
                    rule_type = 'gender'
                elif 'hausnummer' in target_col.lower():
                    rule_type = 'split_number'
                elif 'street' in target_col.lower():
                    rule_type = 'split_street'

            if rule_type == "copy_target" and isinstance(param, str):
                copy_rules[target_col] = param
                continue
        # PASS 2.
        for target_col, _ in target_schema.items():
            rule = self.transformations.get(target_col, {})
            rule_type = rule.get('type') if rule else None
            param = rule.get('param') if rule else None

            source_col = self.mapping_dropdowns[target_col].get() if target_col in self.mapping_dropdowns else None

            if rule_type == "lookup_plz_by_city":
                city_source_col: Optional[str] = str(param) if (param and str(param) in self.source_df.columns) else source_col
                
                def fill_plz(row: pd.Series) -> str:
                    assert self.source_df is not None
                    val: Any = row[source_col] if (source_col and source_col in self.source_df.columns) else None
                    if pd.notna(val) and str(val).strip():
                        return str(val).strip().zfill(PADDING_S)
                    
                    if city_source_col and city_source_col in self.source_df.columns:
                        city_val: Any = row[city_source_col]
                        if pd.notna(city_val) and str(city_val).strip():
                            found_plz: Optional[str] = self.plz_service.get_plz_by_city(str(city_val))
                            if found_plz:
                                return found_plz
                    return default_empty_value

                out_df[target_col] = self.source_df.apply(fill_plz, axis=1)
                
            elif rule_type == "auto_sequence_6":
                # Überprüfen, ob der Nutzer eine Quellspalte im Dropdown ausgewählt hat
                if source_col and source_col in self.source_df.columns and source_col != "-- Nicht zuordnen / Spezielle Regel --":
                    mapped_source_cols.add(source_col)
                    # Übernehme existierende IDs aus der Quelldatei
                    existing_ids = self.source_df[source_col].astype(str).str.strip()
                    
                    # Generiere Sequenz (000001, 000002, ...) als Fallback für Lücken/Leereinträge
                    fallback_seq = [str(i + 1).zfill(6) for i in range(row_count)]
                    
                    # Behalte bestehende IDs; fülle Lücken (NaN/Leerstr) mit der Sequenz auf
                    def_mask = existing_ids.isin(["", "nan", "None", "NULL"]) | existing_ids.isna()
                    out_df[target_col] = [fallback_seq[i] if def_mask.iloc[i] else existing_ids.iloc[i] for i in range(row_count)]
                else:
                    # Keine Quellspalte zugewiesen -> Rein fortlaufende 6-stellige Nummerierung
                    out_df[target_col] = [str(i + 1).zfill(6) for i in range(row_count)]

            elif rule_type == "lookup_city_by_plz":
                plz_source_col: Optional[str] = str(param) if (param and str(param) in self.source_df.columns) else source_col

                def fill_city(row: pd.Series) -> str:
                    assert self.source_df is not None
                    val: Any = row[source_col] if (source_col and source_col in self.source_df.columns) else None
                    if pd.notna(val) and str(val).strip():
                        return str(val).strip()

                    if plz_source_col and plz_source_col in self.source_df.columns:
                        plz_val: Any = row[plz_source_col]
                        if pd.notna(plz_val) and str(plz_val).strip():
                            found_city: Optional[str] = self.plz_service.get_city_by_plz(str(plz_val))
                            if found_city:
                                return found_city
                    return default_empty_value

                out_df[target_col] = self.source_df.apply(fill_city, axis=1)

            elif rule_type == "lookup_ik_provider":
                ik_source_col: Optional[str] = str(param) if (param and str(param) in self.source_df.columns) else source_col
                
                if ik_source_col and ik_source_col in self.source_df.columns:
                    ik_service: Any = getattr(self, 'ik_service', None)

                    def resolve_ik(val: Any) -> str:
                        if pd.isna(val) or not str(val).strip():
                            return default_empty_value
                        
                        cleaned_ik: str = str(val).strip().split('.')[0]
                        
                        if ik_service:
                            provider_name: Optional[str] = ik_service.get_provider_by_ik(cleaned_ik)
                            return provider_name if provider_name else default_empty_value
                        return default_empty_value

                    out_df[target_col] = self.source_df[ik_source_col].apply(resolve_ik)
                else:
                    out_df[target_col] = default_empty_value
                    
            elif rule_type == "validate_ik":
                if source_col and source_col in self.source_df.columns:
                    def check_ik_val(val: Any) -> str:
                        if pd.isna(val) or not str(val).strip():
                            return default_empty_value
                        cleaned_ik: str = str(val).strip().split('.')[0].zfill(9)
                        return cleaned_ik if validate_ik_number(cleaned_ik) else default_empty_value

                    out_df[target_col] = self.source_df[source_col].apply(check_ik_val)
                else:
                    out_df[target_col] = default_empty_value

            elif rule_type == "validate_kvnr":
                if source_col and source_col in self.source_df.columns:
                    def check_kvnr_val(val: Any) -> str:
                        if pd.isna(val) or not str(val).strip():
                            return default_empty_value
                        cleaned_kvnr: str = str(val).strip().upper()
                        return cleaned_kvnr if validate_insurance_number(cleaned_kvnr) else default_empty_value

                    out_df[target_col] = self.source_df[source_col].apply(check_kvnr_val)
                else:
                    out_df[target_col] = default_empty_value
                    
            elif rule_type == "validate_email":
                if source_col and source_col in self.source_df.columns:
                    def check_email_val(val: Any) -> str:
                        if pd.isna(val) or not str(val).strip():
                            return default_empty_value
                        cleaned_email: str = str(val).strip()
                        return cleaned_email if validate_email(cleaned_email) else default_empty_value

                    out_df[target_col] = self.source_df[source_col].apply(check_email_val)
                else:
                    out_df[target_col] = default_empty_value
            
            elif rule_type == "static_value":
                static_val: str = str(rule.get('param', ''))
                out_df[target_col] = static_val
                if source_col != "-- Nicht zuordnen / Spezielle Regel --" and source_col:
                    mapped_source_cols.add(source_col)

            elif rule_type == "generate_uid":
                out_df[target_col] = [generate_id() for _ in range(row_count)]
                if source_col != "-- Nicht zuordnen / Spezielle Regel --" and source_col:
                    mapped_source_cols.add(source_col)

            elif source_col and source_col != "-- Nicht zuordnen / Spezielle Regel --":
                mapped_source_cols.add(source_col)
                series: pd.Series = self.source_df[source_col].copy()

                is_email: bool = rule_type == "validate_email" or any(k in target_col.lower() for k in ['email', 'mail'])
                is_city: bool = any(k in target_col.lower() for k in ['ort', 'city', 'stadt'])
                is_name: bool = any(k in target_col.lower() for k in ['name', 'vname'])
                
                # Hilfsfunktionen für Pandas Apply
                def _sanitize_email(val: Any) -> str:
                    return str(val).strip() if pd.notna(val) else ""

                def _sanitize_city(val: Any) -> str:
                    return sanitize_data_string(str(val), remove_special_chars=False)

                def _sanitize_general(val: Any) -> str:
                    return sanitize_data_string(str(val), remove_special_chars=is_name)

                if is_email:
                    series = series.apply(_sanitize_email)
                elif is_city:
                    series = series.apply(_sanitize_city)
                else:
                    series = series.apply(_sanitize_general)

                if rule_type == "format_date" or 'birth' in target_col.lower() or 'datum' in target_col.lower():
                    date_fallback: str = str(rule.get('param', '')).strip() if rule.get('param') else ""
                    
                    def _apply_date_fallback(val: Any) -> Any:
                        return date_fallback if pd.isna(val) or str(val).strip() in ['', 'nan', 'null', 'None'] else val
                    
                    if date_fallback:
                        series = series.apply(_apply_date_fallback)
                    series = series.apply(format_date_iso)

                elif rule_type == "default_value":
                    fallback_val: str = str(rule.get('param', ''))
                    
                    def _apply_default_fallback(val: Any) -> Any:
                        return fallback_val if pd.isna(val) or str(val).strip() in ['', 'nan', 'null', 'None'] else val
                    
                    series = series.apply(_apply_default_fallback)

                elif rule_type == "clean_plz":
                    def format_plz(val: Any) -> str:
                        val_str: str = str(val).strip() if pd.notna(val) else ""
                        if not val_str or val_str.lower() in ['nan', 'null', 'none', '']:
                            return ""
                        cleaned: str = re.sub(r'\.0$', '', val_str)
                        if cleaned.isdigit() and len(cleaned) <= PADDING_S:
                            return cleaned.zfill(PADDING_S)
                        return cleaned
                    series = series.apply(format_plz)

                elif rule_type == "gender":
                    mapping_dict: Dict[str, str] = {
                        "M": "Herr", "m": "Herr", "HERR": "Herr", "Herr": "Herr", "männlich": "Herr", "1": "Herr",
                        "W": "Frau", "w": "Frau", "FRAU": "Frau", "Frau": "Frau", "weiblich": "Frau", "F": "Frau", "f": "Frau", "2": "Frau"
                    }
                    def _map_gender(val: Any) -> str:
                        s_val = str(val).strip()
                        return mapping_dict.get(s_val, s_val if s_val else default_empty_value)
                        
                    series = series.apply(_map_gender)

                elif rule_type == "split_street":
                    def get_street_name(val: Any) -> str:
                        if pd.isna(val) or str(val).lower() in ['nan', 'null', 'none', '']:
                            return ""
                        return re.sub(r'\s*\d+.*$', '', str(val)).strip()
                    series = series.apply(get_street_name)

                elif rule_type == "split_number":
                    def get_house_number(val: Any) -> str:
                        if pd.isna(val) or str(val).lower() in ['nan', 'null', 'none', '']:
                            return ""
                        numbers: List[str] = re.findall(r'\d+.*$', str(val))
                        return "".join(numbers).strip() if numbers else ""
                    series = series.apply(get_house_number)

                elif rule_type == "merge_columns":
                    second_col: Optional[str] = str(rule.get('param')) if rule.get('param') else None
                    if second_col and second_col in self.source_df.columns:
                        mapped_source_cols.add(second_col)

                        def _clean_s2_val(val: Any) -> str:
                            return sanitize_data_string(str(val), remove_special_chars=(is_name or is_city))

                        s2: pd.Series = self.source_df[second_col].astype(str).apply(_clean_s2_val)
                        series = (series + " " + s2).str.strip()

                if self.chk_fill_null.get() and rule_type != "default_value" and not (rule_type == "format_date" and rule.get('param')):
                    series = series.replace(r'^\s*$', "NULL", regex=True).fillna("NULL")

                out_df[target_col] = series

            else:
                if rule_type == "default_value":
                    out_df[target_col] = str(rule.get('param', ''))
                elif rule_type == "format_date" and rule.get('param'):
                    out_df[target_col] = str(rule.get('param'))
                else:
                    out_df[target_col] = default_empty_value
        
        if invalid_records:
            dialog: ValidationFixDialog = ValidationFixDialog(self, invalid_records)
            self.wait_window(dialog)

            if not dialog.is_accepted:
                return

            for item in invalid_records:
                r_idx: Any = item['row_idx']
                col: str = str(item['target_col'])
                action: str = str(item['action'])

                if action == 'clear':
                    out_df.at[r_idx, col] = default_empty_value
                elif action == 'custom':
                    out_df.at[r_idx, col] = item['custom_val'] if item['custom_val'] else default_empty_value

        for target_col, source_target_col in copy_rules.items():
            if source_target_col in out_df.columns:
                out_df[target_col] = out_df[source_target_col].copy()
            else:
                out_df[target_col] = default_empty_value

        out_df = out_df[list(target_schema.keys())]

        # PASS 3: Überlängen-Erfassung
        conflicts: List[Dict[str, Any]] = []
        for target_col, dtype_str in target_schema.items():
            limit: Optional[int] = parse_varchar_limit(dtype_str)
            if limit:
                for r_idx, val in enumerate(out_df[target_col]):
                    val_str: str = str(val)
                    if val_str != "NULL" and pd.notna(val) and len(val_str) > limit:
                        conflicts.append({
                            'row_idx': r_idx,
                            'col_name': target_col,
                            'limit': limit,
                            'orig_val': val_str
                        })

        if conflicts:
            val_dialog: RowValidationDialog = RowValidationDialog(self, conflicts)
            self.wait_window(val_dialog)
            
            if not val_dialog.confirmed:
                return

            resolved_items: List[Dict[str, Any]] = val_dialog.get_resolved_values()
            for res in resolved_items:
                out_df.at[res['row_idx'], res['col_name']] = res['new_val']

        used_source_cols: Set[str] = set()
        for target_col, dropdown in self.mapping_dropdowns.items():
            val_dropdown: str = dropdown.get()
            if val_dropdown and val_dropdown != "-- Nicht zuordnen / Spezielle Regel --":
                used_source_cols.add(val_dropdown)

        for rule in self.transformations.values():
            if rule.get('param'):
                used_source_cols.add(str(rule['param']))

        unmapped_source_cols: List[str] = [str(c) for c in self.source_df.columns if str(c) not in used_source_cols]

        extra_fields_mappings: List[Dict[str, str]] = []
        if unmapped_source_cols and self.combo_schema.get() == "patienten":
            extra_dialog: ExtraFieldsDialog = ExtraFieldsDialog(self, unmapped_source_cols)
            self.wait_window(extra_dialog)

            if extra_dialog.is_accepted:
                extra_fields_mappings = extra_dialog.result_mappings

        export_path: str = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dateien", "*.csv"), ("Excel Dateien", "*.xlsx")]
        )

        if not export_path:
            return
        
        if extra_fields_mappings:
            property_rows: List[Dict[str, Any]] = []
            for item in extra_fields_mappings:
                raw_name: str = item['field_name'].lstrip('#')
                property_id: str = f"#{raw_name}"
                
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
            
            df_pat_property: pd.DataFrame = pd.DataFrame(property_rows)

            patient_ids: Any = out_df['id'] if 'id' in out_df.columns else self.source_df.index

            map_rows: List[Dict[str, Any]] = []
            for item in extra_fields_mappings:
                raw_name = item['field_name'].lstrip('#')
                property_id = f"#{raw_name}"
                src_col: str = item['source_col']

                for p_id, raw_val in zip(patient_ids, self.source_df[src_col]):
                    if pd.notna(raw_val) and str(raw_val).strip() != "":
                        map_rows.append({
                            'id': str(generate_id()),
                            'property_id': property_id,
                            'patienten_id': p_id,
                            'content': str(raw_val).strip()
                        })

            df_pat_property_map: pd.DataFrame = pd.DataFrame(map_rows)

            output_dir: str = os.path.dirname(export_path)

            path_property: str = os.path.join(output_dir, "pat_property.csv")
            path_property_map: str = os.path.join(output_dir, "pat_property_map.csv")

            df_pat_property.to_csv(path_property, index=False, sep=";", encoding="utf-8-sig")
            df_pat_property_map.to_csv(path_property_map, index=False, sep=";", encoding="utf-8-sig")

        _, ext = os.path.splitext(export_path)

        if ext.lower() == ".xlsx":
            writer: pd.ExcelWriter[Workbook | Any] = pd.ExcelWriter(export_path) # type: ignore
            with writer:
                out_df.to_excel(writer, sheet_name="Patienten", index=False) # type: ignore
        else:
            out_df.to_csv(export_path, index=False, sep=";", encoding="utf-8-sig")
            
        if self.combo_schema.get() == "patienten":
            self.show_toast("Die Patientendaten sowie die Zusatzfelder-Tabellen wurden erfolgreich exportiert.", icon="✅")
        elif self.combo_schema.get() == "adressen":
            self.show_toast("Die Adressen wurden erfolgreich exportiert.", icon="✅")
                    
    def run_pre_check_export(self) -> None:
        """Identifiziert und exportiert alle geflaggten, veränderten, automatisch geänderten oder ergänzten Datensätze als Audit-Protokoll."""
        if self.source_df is None:
            messagebox.showerror("Fehler", "Keine Datei geladen!")
            return

        assert self.source_df is not None

        # 1. Aktive Quellspalten ermitteln
        active_source_cols: Set[str] = set()
        if hasattr(self, 'mapping_dropdowns'):
            for combo in self.mapping_dropdowns.values():
                src_col: str = combo.get()
                if src_col and src_col != "-- Nicht zuordnen / Spezielle Regel --" and src_col in self.source_df.columns:
                    active_source_cols.add(src_col)

        for rule in self.transformations.values():
            if rule.get('param'):
                p_col: str = str(rule['param'])
                if p_col in self.source_df.columns:
                    active_source_cols.add(p_col)

        audit_entries: List[Dict[str, Any]] = []
        df_work: pd.DataFrame = self.source_df.copy()

        # 2. String-Bereinigung (mit Vorschau-Dialog, falls vorhanden)
        if hasattr(self, 'var_clean_strings') and self.var_clean_strings.get() and active_source_cols:
            preview_items: List[Dict[str, Any]] = []
            
            for col in active_source_cols:
                for idx, original_val in df_work[col].items():
                    if pd.isna(original_val):
                        continue
                    
                    orig_str: str = str(original_val)
                    if not orig_str.strip():
                        continue

                    cleaned_val: str = sanitize_data_string(orig_str, remove_special_chars=True)
                    
                    if cleaned_val != orig_str:
                        preview_items.append({
                            'row_idx': idx,
                            'col_name': col,
                            'original': orig_str,
                            'cleaned': cleaned_val
                        })
            
            if preview_items:
                self.cleanup_dialog = StringCleanupPreviewDialog(self, preview_items)
                self.wait_window(self.cleanup_dialog)
                
                accepted_changes: Optional[List[Dict[str, Any]]] = self.cleanup_dialog.result
                
                if accepted_changes is None:
                    return
                
                for change in accepted_changes:
                    r: Any = change['row_idx']
                    c: str = str(change['col_name'])
                    df_work.at[r, c] = change['cleaned']
                    audit_entries.append({
                        'Zeile': int(r) + 1,
                        'Zielspalte': c,
                        'Originalwert': change['original'],
                        'Neuer Wert': change['cleaned'],
                        'Aktion / Grund': "String-Bereinigung (Steuerzeichen / Trim)"
                    })

        def add_audit(row_idx: int, target_col: str, orig_val: Any, new_val: Any, action_desc: str) -> None:
            o_str: str = "" if (pd.isna(orig_val) or str(orig_val).strip() in ["", "nan", "None", "NULL"]) else str(orig_val).strip()
            n_str: str = "" if (pd.isna(new_val) or str(new_val).strip() in ["", "nan", "None", "NULL"]) else str(new_val).strip()
            
            # Ignoriere leere Felder, die mit NULL oder leer aufgefüllt wurden (solange keine Warnung vorliegt)
            if not o_str and not n_str and "⚠️" not in action_desc:
                return

            if o_str != n_str or "⚠️" in action_desc:
                audit_entries.append({
                    'Zeile': row_idx + 1,
                    'Zielspalte': target_col,
                    'Originalwert': "" if pd.isna(orig_val) else str(orig_val),
                    'Neuer Wert': "" if pd.isna(new_val) else str(new_val),
                    'Aktion / Grund': action_desc
                })

        row_count: int = len(df_work)
        target_schema_name: str = self.combo_schema.get()
        target_schema: Dict[str, str] = SCHEMAS[target_schema_name]
        default_empty_value: str = "NULL" if self.chk_fill_null.get() else ""

        out_df: pd.DataFrame = pd.DataFrame()
        copy_rules: Dict[str, str] = {}

        if not hasattr(self, 'plz_service'):
            from services.plz_lookup import PLZLookupService
            self.plz_service = PLZLookupService()

        # PRE-PROCESSING / AUTO-VERVOLLSTÄNDIGUNG
        if hasattr(self, 'autocomplete_settings'):
            if self.autocomplete_settings.get("split_title"):
                for target_col, dropdown in self.mapping_dropdowns.items():
                    if 'nachname' in target_col.lower() or 'name' in target_col.lower():
                        src_c = dropdown.get()
                        if src_c and src_c in df_work.columns:
                            res = df_work[src_c].astype(str).apply(extract_title_and_clean_name)
                            has_titel_col = 'titel' in self.mapping_dropdowns
                            titel_list = [t[0] for t in res]
                            clean_name_list = [t[1] for t in res]

                            for r_i in range(row_count):
                                orig_n = df_work.at[r_i, src_c]
                                new_n = clean_name_list[r_i]
                                ext_t = titel_list[r_i]
                                if ext_t:
                                    add_audit(r_i, target_col, orig_n, new_n, f"Titel von Name getrennt (Titel: '{ext_t}')")
                                    if has_titel_col:
                                        add_audit(r_i, 'titel', "", ext_t, "Titel aus Name extrahiert")

                            if has_titel_col:
                                out_df['titel'] = titel_list
                            df_work[src_c] = clean_name_list

            if self.autocomplete_settings.get("clean_kvnr"):
                for target_col, dropdown in self.mapping_dropdowns.items():
                    if 'kvnr' in target_col.lower() or 'versichertennummer' in target_col.lower():
                        src_c = dropdown.get()
                        if src_c and src_c in df_work.columns:
                            for r_i in range(row_count):
                                orig_k = str(df_work.at[r_i, src_c])
                                cleaned_k = orig_k.upper().replace("O", "0")
                                if orig_k != cleaned_k:
                                    add_audit(r_i, target_col, orig_k, cleaned_k, "KVNR bereinigt ('O' -> '0')")
                                df_work.at[r_i, src_c] = cleaned_k

        # PASS 1: Validierungen & Grundtransformationen
        for target_col, _ in target_schema.items():
            rule: Dict[str, Any] = self.transformations.get(target_col, {})
            rule_type: Optional[str] = rule.get('type') if rule else None
            param: Optional[Any] = rule.get('param') if rule else None
            source_col: Optional[str] = self.mapping_dropdowns[target_col].get() if target_col in self.mapping_dropdowns else None

            if rule_type == "validate_ik":
                if source_col and source_col in df_work.columns:
                    for row_idx, val in df_work[source_col].items():
                        if pd.notna(val) and str(val).strip():
                            cleaned_ik: str = str(val).strip().split('.')[0].zfill(9)
                            if str(val) != cleaned_ik:
                                add_audit(row_idx, target_col, val, cleaned_ik, "IK-Nummer auf 9 Stellen formatiert")
                            if not validate_ik_number(cleaned_ik):
                                add_audit(row_idx, target_col, val, cleaned_ik, "⚠️ Validierungswarnung: Ungültige IK-Nummer")
                    out_df[target_col] = df_work[source_col]
                else:
                    out_df[target_col] = default_empty_value

            elif rule_type == "validate_kvnr":
                if source_col and source_col in df_work.columns:
                    out_df[target_col] = df_work[source_col].copy()
                    for row_idx, val in df_work[source_col].items():
                        if pd.notna(val) and str(val).strip():
                            cleaned_kvnr: str = str(val).strip().upper()
                            is_fixed, fixed_kvnr = try_to_fix_insurance_number(cleaned_kvnr)
                            if is_fixed:
                                add_audit(row_idx, target_col, val, fixed_kvnr, "KVNR-Format automatisch korrigiert")
                                out_df.at[row_idx, target_col] = fixed_kvnr
                            if not validate_insurance_number(fixed_kvnr):
                                add_audit(row_idx, target_col, val, fixed_kvnr, "⚠️ Validierungswarnung: Ungültige KVNR")
                else:
                    out_df[target_col] = default_empty_value

            elif rule_type == "validate_email":
                if source_col and source_col in df_work.columns:
                    for row_idx, val in df_work[source_col].items():
                        if pd.notna(val) and str(val).strip():
                            cleaned_email: str = str(val).strip()
                            if not validate_email(cleaned_email):
                                add_audit(row_idx, target_col, val, cleaned_email, "⚠️ Validierungswarnung: Ungültiges E-Mail-Format")
                    out_df[target_col] = df_work[source_col]
                else:
                    out_df[target_col] = default_empty_value

            if not rule_type:
                if 'birth' in target_col.lower() or 'datum' in target_col.lower() or target_col.endswith('_bis'):
                    rule_type = 'format_date'
                elif 'plz' in target_col.lower():
                    rule_type = 'clean_plz'
                elif 'anrede' in target_col.lower():
                    rule_type = 'gender'
                elif 'hausnummer' in target_col.lower():
                    rule_type = 'split_number'
                elif 'street' in target_col.lower():
                    rule_type = 'split_street'

            if rule_type == "copy_target" and isinstance(param, str):
                copy_rules[target_col] = param
                continue

        # PASS 2: Transformationen & Lookups
        for target_col, _ in target_schema.items():
            rule = self.transformations.get(target_col, {})
            rule_type = rule.get('type') if rule else None
            param = rule.get('param') if rule else None
            source_col = self.mapping_dropdowns[target_col].get() if target_col in self.mapping_dropdowns else None

            if rule_type == "lookup_plz_by_city":
                city_source_col: Optional[str] = str(param) if (param and str(param) in df_work.columns) else source_col
                res_plz: List[str] = []
                for r_idx in range(row_count):
                    val = df_work.at[r_idx, source_col] if (source_col and source_col in df_work.columns) else None
                    if pd.notna(val) and str(val).strip():
                        res_plz.append(str(val).strip().zfill(PADDING_S))
                    elif city_source_col and city_source_col in df_work.columns:
                        city_val = df_work.at[r_idx, city_source_col]
                        if pd.notna(city_val) and str(city_val).strip():
                            found_plz = self.plz_service.get_plz_by_city(str(city_val))
                            if found_plz:
                                add_audit(r_idx, target_col, val, found_plz, f"PLZ automatisch ermittelt (aus Ort '{city_val}')")
                                res_plz.append(found_plz)
                            else:
                                res_plz.append(default_empty_value)
                        else:
                            res_plz.append(default_empty_value)
                    else:
                        res_plz.append(default_empty_value)
                out_df[target_col] = res_plz

            elif rule_type == "auto_sequence_6":
                if source_col and source_col in df_work.columns and source_col != "-- Nicht zuordnen / Spezielle Regel --":
                    existing_ids = df_work[source_col].astype(str).str.strip()
                    fallback_seq = [str(i + 1).zfill(6) for i in range(row_count)]
                    res_seq = []
                    for r_idx in range(row_count):
                        e_id = existing_ids.iloc[r_idx]
                        if e_id in ["", "nan", "None", "NULL"] or pd.isna(df_work.at[r_idx, source_col]):
                            new_s = fallback_seq[r_idx]
                            add_audit(r_idx, target_col, e_id, new_s, "Fortlaufende Nummer ergänzt")
                            res_seq.append(new_s)
                        else:
                            res_seq.append(e_id)
                    out_df[target_col] = res_seq
                else:
                    seq_list = [str(i + 1).zfill(6) for i in range(row_count)]
                    for r_idx in range(row_count):
                        add_audit(r_idx, target_col, "", seq_list[r_idx], "Fortlaufende Nummer generiert")
                    out_df[target_col] = seq_list

            elif rule_type == "lookup_city_by_plz":
                plz_source_col: Optional[str] = str(param) if (param and str(param) in df_work.columns) else source_col
                res_city: List[str] = []
                for r_idx in range(row_count):
                    val = df_work.at[r_idx, source_col] if (source_col and source_col in df_work.columns) else None
                    if pd.notna(val) and str(val).strip():
                        res_city.append(str(val).strip())
                    elif plz_source_col and plz_source_col in df_work.columns:
                        plz_val = df_work.at[r_idx, plz_source_col]
                        if pd.notna(plz_val) and str(plz_val).strip():
                            found_city = self.plz_service.get_city_by_plz(str(plz_val))
                            if found_city:
                                add_audit(r_idx, target_col, val, found_city, f"Ort automatisch ermittelt (aus PLZ '{plz_val}')")
                                res_city.append(found_city)
                            else:
                                res_city.append(default_empty_value)
                        else:
                            res_city.append(default_empty_value)
                    else:
                        res_city.append(default_empty_value)
                out_df[target_col] = res_city

            elif rule_type == "lookup_ik_provider":
                ik_source_col: Optional[str] = str(param) if (param and str(param) in df_work.columns) else source_col
                if ik_source_col and ik_source_col in df_work.columns:
                    ik_service = getattr(self, 'ik_service', None)
                    res_ik: List[str] = []
                    for r_idx, val in df_work[ik_source_col].items():
                        if pd.isna(val) or not str(val).strip():
                            res_ik.append(default_empty_value)
                        else:
                            c_ik = str(val).strip().split('.')[0]
                            p_name = ik_service.get_provider_by_ik(c_ik) if ik_service else None
                            if p_name:
                                add_audit(r_idx, target_col, val, p_name, f"Krankenkasse ermittelt (IK '{c_ik}')")
                                res_ik.append(p_name)
                            else:
                                res_ik.append(default_empty_value)
                    out_df[target_col] = res_ik
                else:
                    out_df[target_col] = default_empty_value

            elif rule_type == "generate_uid":
                uids = [generate_id() for _ in range(row_count)]
                for r_idx in range(row_count):
                    add_audit(r_idx, target_col, "", uids[r_idx], "Automatische UID generiert")
                out_df[target_col] = uids

            elif source_col and source_col != "-- Nicht zuordnen / Spezielle Regel --" and source_col in df_work.columns:
                series: pd.Series = df_work[source_col].copy()
                is_email: bool = rule_type == "validate_email" or any(k in target_col.lower() for k in ['email', 'mail'])
                is_city: bool = any(k in target_col.lower() for k in ['ort', 'city', 'stadt'])
                is_name: bool = any(k in target_col.lower() for k in ['name', 'vname'])

                for r_idx, orig_val in series.items():
                    val_str = str(orig_val) if pd.notna(orig_val) else ""
                    new_val_str = val_str

                    if is_email:
                        new_val_str = val_str.strip()
                    elif is_city:
                        new_val_str = sanitize_data_string(val_str, remove_special_chars=False)
                    else:
                        new_val_str = sanitize_data_string(val_str, remove_special_chars=is_name)

                    if rule_type == "format_date" or 'birth' in target_col.lower() or 'datum' in target_col.lower():
                        date_fallback = str(rule.get('param', '')).strip() if rule.get('param') else ""
                        if date_fallback and (not new_val_str or new_val_str.lower() in ['nan', 'null', 'none']):
                            new_val_str = date_fallback
                            add_audit(r_idx, target_col, orig_val, date_fallback, "Datums-Fallback gesetzt")
                        formatted = format_date_iso(new_val_str)
                        if formatted != val_str:
                            add_audit(r_idx, target_col, orig_val, formatted, "Datumsformatierung (ISO)")
                        new_val_str = formatted

                    elif rule_type == "default_value":
                        fallback_val = str(rule.get('param', ''))
                        if not new_val_str or new_val_str.lower() in ['nan', 'null', 'none']:
                            new_val_str = fallback_val
                            add_audit(r_idx, target_col, orig_val, fallback_val, "Standardwert gesetzt")

                    elif rule_type == "clean_plz":
                        c_plz = new_val_str.strip()
                        if c_plz and c_plz.lower() not in ['nan', 'null', 'none']:
                            c_plz = re.sub(r'\.0$', '', c_plz)
                            if c_plz.isdigit() and len(c_plz) <= PADDING_S:
                                c_plz = c_plz.zfill(PADDING_S)
                        else:
                            c_plz = ""
                        if c_plz != val_str:
                            add_audit(r_idx, target_col, orig_val, c_plz, "PLZ bereinigt / 5-stellig aufgefüllt")
                        new_val_str = c_plz

                    elif rule_type == "gender":
                        mapping_dict = {
                            "M": "Herr", "m": "Herr", "HERR": "Herr", "Herr": "Herr", "männlich": "Herr", "1": "Herr",
                            "W": "Frau", "w": "Frau", "FRAU": "Frau", "Frau": "Frau", "weiblich": "Frau", "F": "Frau", "f": "Frau", "2": "Frau"
                        }
                        mapped_g = mapping_dict.get(new_val_str.strip(), new_val_str.strip() if new_val_str.strip() else default_empty_value)
                        if mapped_g != val_str:
                            add_audit(r_idx, target_col, orig_val, mapped_g, "Anrede/Geschlecht automatisch zugewiesen")
                        new_val_str = mapped_g

                    elif rule_type == "split_street":
                        street_name = re.sub(r'\s*\d+.*$', '', new_val_str).strip() if new_val_str else ""
                        if street_name != val_str:
                            add_audit(r_idx, target_col, orig_val, street_name, "Straßenname extrahiert")
                        new_val_str = street_name

                    elif rule_type == "split_number":
                        numbers = re.findall(r'\d+.*$', new_val_str) if new_val_str else []
                        house_num = "".join(numbers).strip() if numbers else ""
                        if house_num != val_str:
                            add_audit(r_idx, target_col, orig_val, house_num, "Hausnummer extrahiert")
                        new_val_str = house_num

                    if self.chk_fill_null.get() and not new_val_str:
                        new_val_str = "NULL"

                    out_df.at[r_idx, target_col] = new_val_str
            else:
                if rule_type == "default_value":
                    def_val = str(rule.get('param', ''))
                    out_df[target_col] = def_val
                else:
                    out_df[target_col] = default_empty_value

        # Copy target rules
        for target_col, source_target_col in copy_rules.items():
            if source_target_col in out_df.columns:
                out_df[target_col] = out_df[source_target_col].copy()

        # PASS 3: Überlängen-Erfassung (VARCHAR Limits)
        for target_col, dtype_str in target_schema.items():
            limit = parse_varchar_limit(dtype_str)
            if limit and target_col in out_df.columns:
                for r_idx, val in enumerate(out_df[target_col]):
                    val_str = str(val)
                    if val_str != "NULL" and pd.notna(val) and len(val_str) > limit:
                        add_audit(r_idx, target_col, val_str, val_str[:limit], f"⚠️ Wert überschreitet VARCHAR-Limit ({limit}) und wird gekürzt")

        if not audit_entries:
            self.show_toast("Prüfung abgeschlossen: Keine Abweichungen oder geflaggten Datensätze gefunden!", icon="✅")
            return

        audit_df: pd.DataFrame = pd.DataFrame(audit_entries)
        audit_df.sort_values(by=['Zeile', 'Zielspalte'], inplace=True)

        export_path: str = filedialog.asksaveasfilename(
            title="Audit-Protokoll der Abweichungen speichern",
            initialfile="geflaggte_datensaetze_kontrolle.csv",
            defaultextension=".csv",
            filetypes=[("CSV Dateien", "*.csv")]
        )

        if export_path:
            audit_df.to_csv(export_path, index=False, sep=";", encoding="utf-8-sig")
            self.show_toast(f"Audit-Export erfolgreich: {len(audit_df)} Einträge in Protokoll exportiert.", icon="✅")
        
if __name__ == "__main__":
    app = CSVMappingApp()
    app.mainloop()
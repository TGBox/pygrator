import os
import re
import csv
from typing import Any, Dict, List, Optional, Set, cast
from openpyxl import Workbook
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox

# DONE: TODO: Check and verify that the newly added assignments for default connections between columns has worked as intended.
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
# TODO: FEATURE: When a dataset export from another program already has a unique identifier for the individual elements, we want to transfer these values instead of just copying the rolf ID that was generated. (Also we may want to update the program in general, so that the p_nr will be a continuos counter that is easier for humans to reference.)
# TODO: FEATURE: The corrections for the insurance number must only get applied, when we can be sure, that our correction is useful. So we need to add an additional check to calculate the check sum digit at the end, after we applied our correction. And only if the result is viable, we want to change this value!
# TODO: FEATURE: Add a check sum digit calculation for the IK as well.
# TODO: FEATURE: Currently we only account for an empty database on our side. But the program should also be applicable when the database already has values and we get an updated table to update the individual data entries with the new information. Should only update certain fields where a change can be expected. (Maybe add a way to let the user decide, which fields need to adapt to the new source of truth and which will stay the same.)
# TODO: Rename the constants to better reflect their usage throughout the application. Also the names should apply to the elements which are being represented by them and not with the description of the current value. (So we currently have "COL_GREEN", but this could get renamed to "COL_BTN_FG" for example. So that a future change in the appearance of the app wouldn't result in a faulty descriptor for this constant!)
# TODO: Add validation for the values of the fields.
# TODO: Add more comments to this file.
# TODO: Add corrects type annotations to all files.

from db_util import (
    format_date_iso, 
    generate_id, 
    parse_varchar_limit, 
    sanitize_data_string, 
    validate_ik_number, 
    validate_insurance_number, 
    validate_email, 
    extract_flagged_records, 
    try_to_fix_insurance_number
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

    def __init__(self) -> None:
        super().__init__()

        self.title("CSV Data Mapper & Schema Validator")
        center_window(cast(ctk.CTkToplevel, cast(Any, self)), APP_WIDTH, APP_HEIGHT)

        self.source_df = None
        self.source_file_path = ""
        self.transformations = {}  
        self.mapping_dropdowns = {}
        self.trans_buttons = {}
        self.cleanup_dialog = None
        
        self.var_clean_strings = ctk.BooleanVar(value=True)
        
        from services.ik_lookup import IKLookupService
        from services.plz_lookup import PLZLookupService
        
        self.ik_service = IKLookupService()
        self.plz_service = PLZLookupService()

        self._build_ui()

    def _build_ui(self) -> None:
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=PADDING_L, pady=PADDING_M)

        ctk.CTkButton(top_frame, text="Quelldatei laden (CSV)", command=self.load_csv).pack(side="left", padx=PADDING_M, pady=PADDING_M)
        self.lbl_file = ctk.CTkLabel(top_frame, text="Keine Datei ausgewählt", text_color="gray")
        self.lbl_file.pack(side="left", padx=PADDING_M)

        ctk.CTkLabel(top_frame, text="Zielschema:").pack(side="left", padx=(PADDING_XL, PADDING_XS))
        self.combo_schema = ctk.CTkOptionMenu(top_frame, values=list(SCHEMAS.keys()), command=self.on_schema_change)
        self.combo_schema.pack(side="left", padx=PADDING_XS)

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
                text=f"{os.path.basename(file_path)} (Trennzeichen: '{detected_sep}', Encoding: {used_encoding})", 
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
                elif target_col in ("ext_id", "p_nr"):
                    self.transformations[target_col] = {'type': 'copy_target', 'param': "id"}
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

        self.update_all_rule_button_states()
            
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

        ctk.CTkLabel(dialog, text=f"Regel definieren für: '{target_col}'", font=BUTTON_FONT).pack(pady=PADDING_M)

        existing_rule: Dict[str, Any] = self.transformations.get(target_col, {})
        
        default_rule: str = 'none'
        if 'plz' in target_col.lower():
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

        r0 = ctk.CTkRadioButton(dialog, text="🔑 Neue UID generieren (Kompakt)", variable=rule_type, value="generate_uid")
        r0.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        r_copy = ctk.CTkRadioButton(dialog, text="🔗 Wert aus anderer Zielspalte übernehmen", variable=rule_type, value="copy_target")
        r_copy.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        copy_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        copy_frame.pack(anchor="w", padx=PADDING_XXL, pady=2)
        ctk.CTkLabel(copy_frame, text="Kopieren aus:").pack(side="left", padx=PADDING_XS)
        combo_copy_target = ctk.CTkOptionMenu(copy_frame, values=other_target_cols if other_target_cols else ["Keine"])
        combo_copy_target.pack(side="left")
        if existing_rule.get('type') == 'copy_target' and str(existing_rule.get('param')) in other_target_cols:
            combo_copy_target.set(str(existing_rule.get('param')))

        r_date = ctk.CTkRadioButton(dialog, text="📅 Datumsformat anpassen -> YYYY-MM-DD", variable=rule_type, value="format_date")
        r_date.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        date_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        date_frame.pack(anchor="w", padx=PADDING_XXL, pady=2)
        ctk.CTkLabel(date_frame, text="Standardwert bei leeren Feldern (optional):", font=SMALL_LABEL_FONT, text_color=COL_GRAY_70).pack(side="left", padx=PADDING_XS)
        entry_date_default = ctk.CTkEntry(date_frame, width=OPTIONS_MENU_WIDTH, placeholder_text="z. B. 1900-01-01")
        entry_date_default.pack(side="left")
        if existing_rule.get('type') == 'format_date' and existing_rule.get('param'):
            entry_date_default.insert(0, str(existing_rule.get('param')))
        
        separator = ctk.CTkFrame(dialog, height=2, fg_color=COL_GRAY_30)
        separator.pack(fill="x", padx=PADDING_XL, pady=PADDING_M)

        r_default = ctk.CTkRadioButton(dialog, text="✨ Standardwert nur für LEERE Felder setzen", variable=rule_type, value="default_value")
        r_default.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        default_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        default_frame.pack(anchor="w", padx=PADDING_XXL, pady=2)
        ctk.CTkLabel(default_frame, text="Ersatzwert:").pack(side="left", padx=PADDING_XS)
        entry_default_val = ctk.CTkEntry(default_frame, width=VALUE_FIELD_WIDTH, placeholder_text="z. B. Unbekannt")
        entry_default_val.pack(side="left")
        if existing_rule.get('type') == 'default_value':
            entry_default_val.insert(0, str(existing_rule.get('param', '')))

        r_static = ctk.CTkRadioButton(dialog, text="📌 Statischen Festwert für ALLE Zeilen setzen", variable=rule_type, value="static_value")
        r_static.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        static_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        static_frame.pack(anchor="w", padx=PADDING_XXL, pady=2)
        ctk.CTkLabel(static_frame, text="Wert:").pack(side="left", padx=PADDING_XS)
        entry_static_val = ctk.CTkEntry(static_frame, width=VALUE_FIELD_WIDTH)
        entry_static_val.pack(side="left")
        if existing_rule.get('type') == 'static_value':
            entry_static_val.insert(0, str(existing_rule.get('param', '')))

        separator2 = ctk.CTkFrame(dialog, height=2, fg_color=COL_GRAY_30)
        separator2.pack(fill="x", padx=PADDING_XL, pady=PADDING_M)
        
        r_ik_lookup = ctk.CTkRadioButton(
            dialog, 
            text="🏢 Krankenkassenname aus IK-Quellspalte ermitteln", 
            variable=rule_type, 
            value="lookup_ik_provider"
        )
        r_ik_lookup.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        ik_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        ik_frame.pack(anchor="w", padx=PADDING_XXL, pady=2)
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
            dialog, 
            text="✔️ IK-Nummer auf Gültigkeit prüfen (Prüfziffer)", 
            variable=rule_type, 
            value="validate_ik"
        )
        r_val_ik.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        r_val_kvnr = ctk.CTkRadioButton(
            dialog, 
            text="✔️ Krankenversichertennummer (KVNR) auf Gültigkeit prüfen", 
            variable=rule_type, 
            value="validate_kvnr"
        )
        r_val_kvnr.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        r_val_mail = ctk.CTkRadioButton(
            dialog, 
            text="✔️ E-Mailadresse auf Gültigkeit prüfen", 
            variable=rule_type, 
            value="validate_email"
        )
        r_val_mail.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        r_plz = ctk.CTkRadioButton(dialog, text="📮 PLZ bereinigen (.0 entfernen & 5 Stellen)", variable=rule_type, value="clean_plz")
        r_plz.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        r_plz_lookup = ctk.CTkRadioButton(
            dialog, 
            text="📮 PLZ basierend auf Ortsname-Quellspalte ergänzen", 
            variable=rule_type, 
            value="lookup_plz_by_city"
        )
        r_plz_lookup.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        plz_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        plz_frame.pack(anchor="w", padx=PADDING_XXL, pady=2)
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
            dialog, 
            text="🏙️ Ort basierend auf PLZ-Quellspalte ergänzen", 
            variable=rule_type, 
            value="lookup_city_by_plz"
        )
        r_city_lookup.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        city_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        city_frame.pack(anchor="w", padx=PADDING_XXL, pady=2)
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

        r1 = ctk.CTkRadioButton(dialog, text="👫 Geschlecht mappen (M->Herr, W->Frau)", variable=rule_type, value="gender")
        r1.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        separator3 = ctk.CTkFrame(dialog, height=2, fg_color=COL_GRAY_30)
        separator3.pack(fill="x", padx=PADDING_XL, pady=PADDING_M)

        r2 = ctk.CTkRadioButton(dialog, text="🏠 Straße/(Hausnr.) trennen -> Nur Straßenname", variable=rule_type, value="split_street")
        r2.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        r3 = ctk.CTkRadioButton(dialog, text="🔢 (Straße)/Hausnr. trennen -> Nur Hausnummer", variable=rule_type, value="split_number")
        r3.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)
        
        r_merge = ctk.CTkRadioButton(dialog, text="🔗 Zwei Quellspalten zusammenführen (mit Leerzeichen)", variable=rule_type, value="merge_columns")
        r_merge.pack(anchor="w", padx=PADDING_XL, pady=PADDING_XS)

        merge_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        merge_frame.pack(anchor="w", padx=PADDING_XXL, pady=2)
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
            messagebox.showinfo("Gespeichert", f"Regel '{t_type}' für '{target_col}' hinterlegt.")
            dialog.destroy()

        def remove_rule() -> None:
            if target_col in self.transformations:
                del self.transformations[target_col]
            self.update_rule_button_state(target_col)
            messagebox.showinfo("Entfernt", f"Keine Regel mehr für '{target_col}' aktiv.")
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=PADDING_L)
        ctk.CTkButton(btn_frame, text="Speichern", command=save_rule).pack(side="left", padx=PADDING_XS, anchor="s")
        ctk.CTkButton(btn_frame, text="Regel löschen", fg_color="red3", hover_color="red4", command=remove_rule).pack(side="left", padx=PADDING_XS, anchor="s")

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
            messagebox.showinfo("Export erfolgreich", "Die Patientendaten sowie die Zusatzfelder-Tabellen wurden erfolgreich exportiert.")
        elif self.combo_schema.get() == "adressen":
            messagebox.showinfo("Export erfolgreich", "Die Adressen wurden erfolgreich exportiert.")
                    
    def run_pre_check_export(self) -> None:
        """Identifiziert und exportiert geflaggte Datensätze für eine manuelle Kontrolle."""
        if self.source_df is None:
            messagebox.showerror("Fehler", "Keine Datei geladen!")
            return

        assert self.source_df is not None

        target_schema_name: str = self.combo_schema.get()
        target_schema: Dict[str, str] = SCHEMAS[target_schema_name]

        mappings: List[Dict[str, Any]] = []

        for target_col, combo in self.mapping_dropdowns.items():
            source_col: str = combo.get()

            if source_col and source_col != "-- Nicht zuordnen / Spezielle Regel --":
                dtype_str: str = target_schema.get(target_col, "")
                limit: Optional[int] = parse_varchar_limit(dtype_str)

                rule: Dict[str, Any] = self.transformations.get(target_col, {})
                rule_type: Optional[str] = rule.get('type') if rule else None

                mappings.append({
                    'source_col': source_col,
                    'target_col': target_col,
                    'limit': limit,
                    'rule_type': rule_type
                })

        flagged_df: pd.DataFrame = extract_flagged_records(
            df=self.source_df,
            mappings=mappings
        )

        if flagged_df.empty:
            messagebox.showinfo(
                "Prüfung abgeschlossen", 
                "Keine auffälligen Datensätze gefunden!\nAlle zugeordneten Felder sind valide."
            )
            return

        export_path: str = filedialog.asksaveasfilename(
            title="Geflaggte Datensätze speichern",
            initialfile="geflaggte_datensaetze_kontrolle.csv",
            defaultextension=".csv",
            filetypes=[("CSV Dateien", "*.csv")]
        )

        if export_path:
            flagged_df.to_csv(export_path, index=False, sep=";", encoding="utf-8-sig")
            messagebox.showinfo(
                "Export erfolgreich", 
                f"Es wurden {len(flagged_df)} betroffene Datensätze exportiert.\n\n"
                f"Gespeichert unter:\n{export_path}"
            )
        
if __name__ == "__main__":
    app = CSVMappingApp()
    app.mainloop()
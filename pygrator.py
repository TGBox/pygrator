# type: ignore
import os
import re
import pandas as pd
import csv
import customtkinter as ctk
from tkinter import filedialog, messagebox

from db_util import format_date_iso, generate_id, parse_varchar_limit, sanitize_data_string, validate_ik_number, validate_insurance_number, validate_email
from schemas import SCHEMAS
from dialogs import center_window, ExtraFieldsDialog, RowValidationDialog, ValidationFixDialog, StringCleanupPreviewDialog

RULE_NAMES = {
    "generate_uid": "UID generieren",
    "copy_target": "Kopieren aus",
    "format_date": "Datum (YYYY-MM-DD)",
    "default_value": "Standardwert",
    "static_value": "Festwert",
    "clean_plz": "PLZ (5-stellig)",
    "gender": "Geschlecht->Anrede",
    "split_street": "Nur Straße",
    "split_number": "Nur Hausnummer",
    "merge_columns": "Spalten zusammenführen",
    "lookup_ik_provider": "Krankenkasse aus IK",
    "lookup_plz_by_city": "PLZ aus Ort ergänzen",
    "lookup_city_by_plz": "Ort aus PLZ ergänzen",
    "validate_ik": "IK-Nummer prüfen",
    "validate_kvnr": "Versichertennr. prüfen",
    "validate_email": "E-Mail prüfen"
}

# Farbschema & Theme für modernere Optik
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

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
# TODO: Add validation for the values of the fields.
# TODO: Add more comments to this file.
# TODO: Add corrects type annotations to all files.

class CSVMappingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CSV Data Mapper & Schema Validator")
        center_window(self, 1040, 880)

        self.source_df = None
        self.source_file_path = ""
        self.transformations = {}  
        self.mapping_dropdowns = {}
        
        self.var_clean_strings = ctk.BooleanVar(value=True)
        
        from services.ik_lookup import IKLookupService
        from services.plz_lookup import PLZLookupService
        
        self.ik_service = IKLookupService()
        self.plz_service = PLZLookupService()

        self._build_ui()

    def _build_ui(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(top_frame, text="Quelldatei laden (CSV)", command=self.load_csv).pack(side="left", padx=10, pady=10)
        self.lbl_file = ctk.CTkLabel(top_frame, text="Keine Datei ausgewählt", text_color="gray")
        self.lbl_file.pack(side="left", padx=10)

        ctk.CTkLabel(top_frame, text="Zielschema:").pack(side="left", padx=(20, 5))
        self.combo_schema = ctk.CTkOptionMenu(top_frame, values=list(SCHEMAS.keys()), command=self.on_schema_change)
        self.combo_schema.pack(side="left", padx=5)

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Spalten-Zuordnung & Schema-Limits")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # UNTERE BEDIENLEISTE (EXPORT-OPTIONS)
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=15, pady=10)

        # Linker Bereich: Checkboxen
        chk_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        chk_frame.pack(side="left", padx=10, pady=5)

        self.chk_fill_null = ctk.CTkCheckBox(
            chk_frame, 
            text="Unbelegte Felder mit 'NULL' auffüllen (statt leerem Text)"
        )
        self.chk_fill_null.pack(anchor="w", pady=3)
        self.chk_fill_null.select()
        
        chk_clean_strings = ctk.CTkCheckBox(
            chk_frame, 
            text="String-Werte bereinigen (Trim & Steuerzeichen entfernen)",
            variable=self.var_clean_strings
        )
        chk_clean_strings.pack(side="left", pady=5)

        # Mittlerer Bereich: Format & Encoding Auswahlen
        export_opts_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        export_opts_frame.pack(side="left", padx=20, pady=5)

        # Format-Auswahl
        ctk.CTkLabel(export_opts_frame, text="Export-Format:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        self.combo_export_format = ctk.CTkOptionMenu(
            export_opts_frame, 
            values=["CSV (Semikolon ';')", "CSV (Komma ',')", "Excel (.xlsx)"],
            width=160,
            command=self.on_format_change
        )
        self.combo_export_format.grid(row=0, column=1, padx=5, pady=2)

        # Encoding-Auswahl
        ctk.CTkLabel(export_opts_frame, text="Encoding:", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w", padx=5)
        self.combo_encoding = ctk.CTkOptionMenu(
            export_opts_frame, 
            values=["utf-8-sig (Excel CSV)", "utf-8", "cp1252 (Windows)", "iso-8859-1"],
            width=160
        )
        self.combo_encoding.grid(row=1, column=1, padx=5, pady=2)

        # Rechter Bereich: Button Export
        ctk.CTkButton(
            bottom_frame, 
            text="Prüfen & Exportieren", 
            fg_color="green", 
            hover_color="darkgreen",
            font=("Arial", 12, "bold"),
            command=self.start_processing
        ).pack(side="right", padx=10, pady=10)

    def on_format_change(self, choice):
        """Aktiviert/Deaktiviert das Encoding-Dropdown je nach Format."""
        if "Excel" in choice:
            self.combo_encoding.configure(state="disabled")
        else:
            self.combo_encoding.configure(state="normal")
    
    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV/Excel Files", "*.csv;*.txt;*.xlsx;*.xls")])
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        loaded_df = None
        used_encoding = "Binary"
        detected_sep = "N/A"

        if ext in ['.xlsx', '.xls']:
            try:
                loaded_df = pd.read_excel(file_path, dtype=str)
            except Exception as e:
                messagebox.showerror("Fehler beim Laden", f"Konnte Excel-Datei nicht lesen:\n{str(e)}")
                return
        else:
            detected_sep = ';'
            try:
                with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    sample = f.read(4096)
                    sniffer = csv.Sniffer()
                    detected_sep = sniffer.sniff(sample).delimiter
            except Exception:
                pass

            encodings_to_try = ['utf-8-sig', 'utf-8', 'cp1252', 'latin1']
            for enc in encodings_to_try:
                try:
                    loaded_df = pd.read_csv(
                        file_path, 
                        sep=detected_sep, 
                        encoding=enc, 
                        on_bad_lines='skip',
                        dtype=str
                    )
                    used_encoding = enc
                    break
                except Exception:
                    continue

        if loaded_df is not None:
            self.source_df = loaded_df
            self.source_file_path = file_path
            self.lbl_file.configure(
                text=f"{os.path.basename(file_path)} (Trennzeichen: '{detected_sep}', Encoding: {used_encoding})", 
                text_color="white"
            )
            self.render_mapping_rows()
        else:
            messagebox.showerror("Fehler beim Laden", "Konnte die Datei nicht lesen.")

    def on_schema_change(self, choice):
        if self.source_df is not None:
            self.render_mapping_rows()

    def render_mapping_rows(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if self.source_df is None:
            return

        source_cols = ["-- Nicht zuordnen / Spezielle Regel --"] + list(self.source_df.columns)
        target_schema = SCHEMAS[self.combo_schema.get()]

        ctk.CTkLabel(self.scroll_frame, text="Zielspalte (Datentyp)", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self.scroll_frame, text="Quellspalte (CSV)", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(self.scroll_frame, text="Spezielle Transformation", font=("Arial", 12, "bold")).grid(row=0, column=2, padx=10, pady=5, sticky="w")

        self.mapping_dropdowns = {}
        self.trans_buttons = {}

        for idx, (target_col, dtype) in enumerate(target_schema.items(), start=1):
            label_text = f"{target_col} ({dtype})"
            ctk.CTkLabel(self.scroll_frame, text=label_text, font=("Roboto", 11)).grid(row=idx, column=0, padx=10, pady=5, sticky="w")

            combo = ctk.CTkOptionMenu(self.scroll_frame, values=source_cols)
            combo.grid(row=idx, column=1, padx=10, pady=5, sticky="w")
            
            target_lower = target_col.lower()
            
            for src_col in self.source_df.columns:
                src_lower = src_col.lower()

                # A) EXAKTE ÜBEREINSTIMMUNG (Höchste Priorität)
                if src_lower == target_lower:
                    combo.set(src_col)
                    break

                # B) EXPLIZITE SONDERREGELN
                # Telefon & Mobilfunk (Spezifische Zuordnungen verhindern falsche Substring-Matches)
                if target_lower in ["telefonmobil", "mobil", "p_handy"]:
                    if src_lower in ["mobil", "handy", "mobile", "telefonmobil"]:
                        combo.set(src_col)
                        break
                    continue  # Verhindert, dass "telefon" auf "telefonmobil" gematcht wird!

                if target_lower in ["telefon", "p_tel", "tel"]:
                    if src_lower in ["telefon", "p_tel", "tel", "telefon1"]:
                        combo.set(src_col)
                        break

                # Schema "adressen": Namen
                if src_lower == "titel" and "name1" in target_lower:
                    combo.set(src_col)
                    break
                if src_lower == "vorname" and ("name2" in target_lower or "p_vname" in target_lower):
                    combo.set(src_col)
                    break
                if src_lower == "nachname" and ("name3" in target_lower or "p_name" in target_lower):
                    combo.set(src_col)
                    break

                # Weitere Feld-Typen
                if src_lower == "wohnort" and "p_ort" in target_lower:
                    combo.set(src_col)
                    break
                if src_lower == "geburtsdatum" and "p_birth" in target_lower:
                    combo.set(src_col)
                    break
                if src_lower == "geschlecht" and any(k in target_lower for k in ["anrede", "p_anrede"]):
                    combo.set(src_col)
                    break
                if src_lower == "telefon2" and "p_telge" in target_lower:
                    combo.set(src_col)
                    break
                if src_lower in ("strasse", "straße") and any(k in target_lower for k in ["p_street", "p_hausnummer", "strasse", "straße"]):
                    combo.set(src_col)
                    break
                if src_lower == "kas_ik" and "p_ik" in target_lower:
                    combo.set(src_col)
                    break
                if src_lower == "status" and "p_vs" in target_lower:
                    combo.set(src_col)
                    break
                if src_lower == "versichertennummer" and "p_vnr" in target_lower:
                    combo.set(src_col)
                    break

                # C) ALLGEMEINES SUBSTRING-MATCHING (Fallback, nur wenn kein expliziter Ausschluss vorliegt)
                if (src_lower in target_lower or target_lower in src_lower) and len(src_lower) > 3:
                    combo.set(src_col)
                    break

            self.mapping_dropdowns[target_col] = combo

            # --- 2. Automatische Voreinstellung von Regeln im Dict ---
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
                    # Case-insensitive Suche nach der Ortsspalte
                    city_col = next((c for c in self.source_df.columns if c.lower() in ["ort", "wohnort", "stadt"]), None)
                    if city_col:
                        self.transformations[target_col] = {'type': 'lookup_plz_by_city', 'param': city_col}
                    else:
                        self.transformations[target_col] = {'type': 'clean_plz'}
                elif target_col in ("p_ort", "ort"):
                    # Case-insensitive Suche nach der PLZ-Spalte
                    plz_col = next((c for c in self.source_df.columns if "plz" in c.lower()), None)
                    if plz_col:
                        self.transformations[target_col] = {'type': 'lookup_city_by_plz', 'param': plz_col}
                elif "street" in target_col:
                    self.transformations[target_col] = {'type': 'split_street'}
                elif "hausnummer" in target_col:
                    self.transformations[target_col] = {'type': 'split_number'}
                elif target_col == "p_krankenkasse":
                    for src_col in self.source_df.columns:
                        if "ik" in src_col.lower():
                            self.transformations[target_col] = {
                                'type': 'lookup_ik_provider',
                                'param': src_col
                            }
                            break
                elif target_col in ("p_ik", "ik") or "ik_nummer" in target_col:
                    self.transformations[target_col] = {'type': 'validate_ik'}

                elif target_col in ("p_vnr", "vnr", "kvnr") or "versichertennummer" in target_col:
                    self.transformations[target_col] = {'type': 'validate_kvnr'}
                elif target_col in ("p_email", "email", "mail", "Email", "E-Mail"):
                    self.transformations[target_col] = {'type': 'validate_email'}

            # --- 3. Button erstellen & speichern ---
            btn_trans = ctk.CTkButton(
                self.scroll_frame, 
                text="Regel hinzufügen...", 
                width=240,
                fg_color="gray30",
                command=lambda t=target_col: self.open_transformation_dialog(t)
            )
            btn_trans.grid(row=idx, column=2, padx=10, pady=5, sticky="w")
            self.trans_buttons[target_col] = btn_trans

        # --- 4. NACHDEM ALLE BUTTONS ERZEUGT WURDEN: Farben/Texte updaten ---
        self.update_all_rule_button_states()
            
    def update_all_rule_button_states(self):
        """Aktualisiert die Button-Texte und -Farben für ALLE Zielspalten."""
        if hasattr(self, 'trans_buttons'):
            for target_col in self.trans_buttons.keys():
                self.update_rule_button_state(target_col)
            
    def update_rule_button_state(self, target_col: str):
        """Aktualisiert Text und Farbe des Buttons je nachdem, ob eine Regel gesetzt ist."""
        btn = self.trans_buttons.get(target_col)
        if not btn:
            return

        rule = self.transformations.get(target_col, {})
        
        # Falls die Regel direkt als String gespeichert wurde (z.B. 'generate_uid')
        if isinstance(rule, str):
            rule_type = rule
            param = None
        elif isinstance(rule, dict):
            rule_type = rule.get('type')
            param = rule.get('param')
        else:
            rule_type = None
            param = None

        if rule_type and rule_type != "none":
            # Regel-Bezeichnung holen
            rule_title = RULE_NAMES.get(rule_type, rule_type)
            
            # Text für Button zusammenbauen
            if param:
                button_text = f"✓ {rule_title} (\"{param}\")"
            else:
                button_text = f"✓ {rule_title}"

            # Grüner Button mit sprechendem Regel-Text
            btn.configure(
                text=button_text,
                fg_color="#1E7E34",        # Dunkelgrün
                hover_color="#145A24"
            )
        else:
            # Standardzustand ohne Regel
            btn.configure(
                text="Regel hinzufügen...",
                fg_color="gray30",
                hover_color="gray40"
            )

    def open_transformation_dialog(self, target_col):
        target_schema = SCHEMAS[self.combo_schema.get()]
        other_target_cols = [col for col in target_schema.keys() if col != target_col]

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Transformation für '{target_col}'")
        center_window(dialog, 540, 950)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Regel definieren für: '{target_col}'", font=("Arial", 12, "bold")).pack(pady=10)

        existing_rule = self.transformations.get(target_col, {})
        
        default_rule = 'none'
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

        current_type = existing_rule.get('type', default_rule)
        rule_type = ctk.StringVar(value=current_type)

        r0 = ctk.CTkRadioButton(dialog, text="🔑 Neue UID generieren (Kompakt)", variable=rule_type, value="generate_uid")
        r0.pack(anchor="w", padx=20, pady=5)
        
        r_copy = ctk.CTkRadioButton(dialog, text="🔗 Wert aus anderer Zielspalte übernehmen", variable=rule_type, value="copy_target")
        r_copy.pack(anchor="w", padx=20, pady=5)

        copy_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        copy_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(copy_frame, text="Kopieren aus:").pack(side="left", padx=5)
        combo_copy_target = ctk.CTkOptionMenu(copy_frame, values=other_target_cols if other_target_cols else ["Keine"])
        combo_copy_target.pack(side="left")
        if existing_rule.get('type') == 'copy_target' and existing_rule.get('param') in other_target_cols:
            combo_copy_target.set(existing_rule.get('param'))

        r_date = ctk.CTkRadioButton(dialog, text="📅 Datumsformat anpassen -> YYYY-MM-DD", variable=rule_type, value="format_date")
        r_date.pack(anchor="w", padx=20, pady=5)

        date_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        date_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(date_frame, text="Standardwert bei leeren Feldern (optional):", font=("Arial", 10), text_color="gray70").pack(side="left", padx=5)
        entry_date_default = ctk.CTkEntry(date_frame, width=160, placeholder_text="z. B. 1900-01-01")
        entry_date_default.pack(side="left")
        if existing_rule.get('type') == 'format_date' and existing_rule.get('param'):
            entry_date_default.insert(0, str(existing_rule.get('param')))
        
        separator = ctk.CTkFrame(dialog, height=2, fg_color="gray30")
        separator.pack(fill="x", padx=20, pady=10)

        r_default = ctk.CTkRadioButton(dialog, text="✨ Standardwert nur für LEERE Felder setzen", variable=rule_type, value="default_value")
        r_default.pack(anchor="w", padx=20, pady=5)

        default_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        default_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(default_frame, text="Ersatzwert:").pack(side="left", padx=5)
        entry_default_val = ctk.CTkEntry(default_frame, width=200, placeholder_text="z. B. Unbekannt")
        entry_default_val.pack(side="left")
        if existing_rule.get('type') == 'default_value':
            entry_default_val.insert(0, str(existing_rule.get('param', '')))

        r_static = ctk.CTkRadioButton(dialog, text="📌 Statischen Festwert für ALLE Zeilen setzen", variable=rule_type, value="static_value")
        r_static.pack(anchor="w", padx=20, pady=5)

        static_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        static_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(static_frame, text="Wert:").pack(side="left", padx=5)
        entry_static_val = ctk.CTkEntry(static_frame, width=200)
        entry_static_val.pack(side="left")
        if existing_rule.get('type') == 'static_value':
            entry_static_val.insert(0, str(existing_rule.get('param', '')))

        
        separator2 = ctk.CTkFrame(dialog, height=2, fg_color="gray30")
        separator2.pack(fill="x", padx=20, pady=10)
        
        # Radiobutton & UI für IK-Lookup hinzufügen
        r_ik_lookup = ctk.CTkRadioButton(
            dialog, 
            text="🏢 Krankenkassenname aus IK-Quellspalte ermitteln", 
            variable=rule_type, 
            value="lookup_ik_provider"
        )
        r_ik_lookup.pack(anchor="w", padx=20, pady=5)

        ik_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        ik_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(ik_frame, text="IK-Quellspalte:").pack(side="left", padx=5)

        source_cols_list = list(self.source_df.columns) if self.source_df is not None else []
        combo_ik_source = ctk.CTkOptionMenu(ik_frame, values=source_cols_list if source_cols_list else ["Keine"])
        combo_ik_source.pack(side="left")

        # Falls diese Regel bereits gesetzt war, Vorauswahl wiederherstellen:
        if existing_rule.get('type') == 'lookup_ik_provider' and existing_rule.get('param') in source_cols_list:
            combo_ik_source.set(existing_rule.get('param'))
        elif self.source_df is not None:
            # Versuche automatisch die spalte kas_ik vorauszuauswählen, falls vorhanden
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
        r_val_ik.pack(anchor="w", padx=20, pady=5)

        r_val_kvnr = ctk.CTkRadioButton(
            dialog, 
            text="✔️ Krankenversichertennummer (KVNR) auf Gültigkeit prüfen", 
            variable=rule_type, 
            value="validate_kvnr"
        )
        r_val_kvnr.pack(anchor="w", padx=20, pady=5)
        
        r_val_mail = ctk.CTkRadioButton(
            dialog, 
            text="✔️ E-Mailadresse auf Gültigkeit prüfen", 
            variable=rule_type, 
            value="validate_email"
        )
        r_val_mail.pack(anchor="w", padx=20, pady=5)

        r_plz = ctk.CTkRadioButton(dialog, text="📮 PLZ bereinigen (.0 entfernen & 5 Stellen)", variable=rule_type, value="clean_plz")
        r_plz.pack(anchor="w", padx=20, pady=5)
        
        r_plz_lookup = ctk.CTkRadioButton(
            dialog, 
            text="📮 PLZ basierend auf Ortsname-Quellspalte ergänzen", 
            variable=rule_type, 
            value="lookup_plz_by_city"
        )
        r_plz_lookup.pack(anchor="w", padx=20, pady=5)

        plz_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        plz_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(plz_frame, text="Ortsname-Quellspalte:").pack(side="left", padx=5)
        combo_city_source = ctk.CTkOptionMenu(plz_frame, values=source_cols_list if source_cols_list else ["Keine"])
        combo_city_source.pack(side="left")

        # AUTO-MATCH für Orts-Spalte im Dialog:
        if existing_rule.get('type') == 'lookup_plz_by_city' and existing_rule.get('param') in source_cols_list:
            combo_city_source.set(existing_rule.get('param'))
        elif self.source_df is not None:
            for c in source_cols_list:
                if c.lower() in ["ort", "wohnort", "stadt"]:
                    combo_city_source.set(c)
                    break

        # --- Ort aus PLZ Lookup UI ---
        r_city_lookup = ctk.CTkRadioButton(
            dialog, 
            text="🏙️ Ort basierend auf PLZ-Quellspalte ergänzen", 
            variable=rule_type, 
            value="lookup_city_by_plz"
        )
        r_city_lookup.pack(anchor="w", padx=20, pady=5)

        city_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        city_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(city_frame, text="PLZ-Quellspalte:").pack(side="left", padx=5)
        combo_plz_source = ctk.CTkOptionMenu(city_frame, values=source_cols_list if source_cols_list else ["Keine"])
        combo_plz_source.pack(side="left")

        # AUTO-MATCH für PLZ-Spalte im Dialog:
        if existing_rule.get('type') == 'lookup_city_by_plz' and existing_rule.get('param') in source_cols_list:
            combo_plz_source.set(existing_rule.get('param'))
        elif self.source_df is not None:
            for c in source_cols_list:
                if "plz" in c.lower():
                    combo_plz_source.set(c)
                    break

        r1 = ctk.CTkRadioButton(dialog, text="👫 Geschlecht mappen (M->Herr, W->Frau)", variable=rule_type, value="gender")
        r1.pack(anchor="w", padx=20, pady=5)
        
        separator3 = ctk.CTkFrame(dialog, height=2, fg_color="gray30")
        separator3.pack(fill="x", padx=20, pady=10)

        r2 = ctk.CTkRadioButton(dialog, text="🏠 Straße/(Hausnr.) trennen -> Nur Straßenname", variable=rule_type, value="split_street")
        r2.pack(anchor="w", padx=20, pady=5)

        r3 = ctk.CTkRadioButton(dialog, text="🔢 (Straße)/Hausnr. trennen -> Nur Hausnummer", variable=rule_type, value="split_number")
        r3.pack(anchor="w", padx=20, pady=5)
        
        r_merge = ctk.CTkRadioButton(dialog, text="🔗 Zwei Quellspalten zusammenführen (mit Leerzeichen)", variable=rule_type, value="merge_columns")
        r_merge.pack(anchor="w", padx=20, pady=5)

        merge_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        merge_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(merge_frame, text="Zweite Quellspalte:").pack(side="left", padx=5)

        source_cols_list = list(self.source_df.columns) if self.source_df is not None else []
        combo_merge_source = ctk.CTkOptionMenu(merge_frame, values=source_cols_list if source_cols_list else ["Keine"])
        combo_merge_source.pack(side="left")

        if existing_rule.get('type') == 'merge_columns' and existing_rule.get('param') in source_cols_list:
            combo_merge_source.set(existing_rule.get('param'))

        def save_rule():
            t_type = rule_type.get()
            param = None

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
            self.update_rule_button_state(target_col)  # <--- NEU: Visuellen Status updaten
            messagebox.showinfo("Gespeichert", f"Regel '{t_type}' für '{target_col}' hinterlegt.")
            dialog.destroy()

        def remove_rule():
            if target_col in self.transformations:
                del self.transformations[target_col]
            self.update_rule_button_state(target_col)  # <--- NEU: Visuellen Status updaten
            messagebox.showinfo("Entfernt", f"Keine Regel mehr für '{target_col}' aktiv.")
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="Speichern", command=save_rule).pack(side="left", padx=5, anchor="s")
        ctk.CTkButton(btn_frame, text="Regel löschen", fg_color="red3", hover_color="red4", command=remove_rule).pack(side="left", padx=5, anchor="s")

    def start_processing(self):
        """Startet den Gesamtablauf: Prüft Vorschaudialog und führt danach den Export aus."""
        
        if self.source_df is None:
            messagebox.showerror("Fehler", "Keine Datei geladen!")
            return

        # ---------------------------------------------------------------------
        # SCHRITT 1: Nur relevante Spalten ermitteln, die im Schema genutzt werden
        # ---------------------------------------------------------------------
        # Wir sammeln alle Quellspalten, die in der Mapping-Tabelle zugewiesen sind
        active_source_cols = set()
        
        # 1. Aus den aktiven Dropdowns im Schema abfragen
        if hasattr(self, 'mapping_dropdowns'):
            for combo in self.mapping_dropdowns.values():
                src_col = combo.get()
                if src_col and src_col != "-- Nicht zuordnen / Spezielle Regel --" and src_col in self.source_df.columns:
                    active_source_cols.add(src_col)

        # 2. Zusätzlich Spalten berücksichtigen, die in Transformations-Parametern gewählt wurden (z.B. bei PLZ-, IK- oder Ort-Lookups)
        for rule in self.transformations.values():
            if isinstance(rule, dict) and rule.get('param'):
                p_col = rule['param']
                if p_col in self.source_df.columns:
                    active_source_cols.add(p_col)

        # Falls gar keine Zuordnungen getroffen wurden, Abbruch/keine Bereinigung nötig
        if not active_source_cols:
            self.process_and_export()
            return

        # ---------------------------------------------------------------------
        # SCHRITT 2: String-Bereinigung NUR für relevante Spalten prüfen
        # ---------------------------------------------------------------------
        if hasattr(self, 'var_clean_strings') and self.var_clean_strings.get():
            preview_items = []
            
            # Suchen nach betroffenen Zellen NUR in den aktiven Spalten
            for col in active_source_cols:
                for idx, original_val in self.source_df[col].items():
                    if pd.isna(original_val):
                        continue
                    
                    orig_str = str(original_val)
                    if not orig_str.strip():
                        continue

                    cleaned_val = sanitize_data_string(orig_str, remove_special_chars=True)
                    
                    if cleaned_val != orig_str:
                        preview_items.append({
                            'row_idx': idx,
                            'col_name': col,
                            'original': orig_str,
                            'cleaned': cleaned_val
                        })
            
            # Vorschau-Dialog NUR anzeigen, wenn bei den RELEVANTEN Spalten Änderungen vorliegen
            if preview_items:
                self.cleanup_dialog = StringCleanupPreviewDialog(self, preview_items)
                self.wait_window(self.cleanup_dialog)
                
                accepted_changes = self.cleanup_dialog.result
                
                # ABBRUCH durch den Nutzer
                if accepted_changes is None:
                    return
                
                # Nur die vom Nutzer bestätigten Bereinigungen übernehmen
                for change in accepted_changes:
                    r = change['row_idx']
                    c = change['col_name']
                    self.source_df.at[r, c] = change['cleaned']

        # ---------------------------------------------------------------------
        # SCHRITT 3: Export ausführen
        # ---------------------------------------------------------------------
        self.process_and_export()

    def process_and_export(self):
        if self.source_df is None:
            messagebox.showerror("Fehler", "Keine Datei geladen!")
            return

        out_df = pd.DataFrame()
        mapped_source_cols = set()
        row_count = len(self.source_df)

        target_schema = SCHEMAS[self.combo_schema.get()]
        default_empty_value = "NULL" if self.chk_fill_null.get() else ""

        copy_rules = {}
        invalid_records = []
        
        if not hasattr(self, 'plz_service'):
            from services.plz_lookup import PLZLookupService
            self.plz_service = PLZLookupService()

        # PASS 1: Transformationen ausführen
        for target_col, dtype in target_schema.items():
            rule = self.transformations.get(target_col, {})
            rule_type = rule.get('type') if isinstance(rule, dict) else rule
            param = rule.get('param') if isinstance(rule, dict) else None
            source_col = self.mapping_dropdowns[target_col].get() if target_col in self.mapping_dropdowns else None

            # --- Validierung IK-Nummer ---
            if rule_type == "validate_ik":
                if source_col and source_col in self.source_df.columns:
                    for row_idx, val in self.source_df[source_col].items():
                        if pd.notna(val) and str(val).strip():
                            cleaned_ik = str(val).strip().split('.')[0].zfill(9)
                            if not validate_ik_number(cleaned_ik):
                                invalid_records.append({
                                    'row_idx': row_idx,
                                    'target_col': target_col,
                                    'rule_type': rule_type,
                                    'original_val': str(val),
                                    'action': 'keep',
                                    'custom_val': ''
                                })
                    # Vorerst Standardwerte/Rohwerte übernehmen
                    out_df[target_col] = self.source_df[source_col]
                else:
                    out_df[target_col] = default_empty_value

            # --- Validierung Versichertennummer (KVNR) ---
            elif rule_type == "validate_kvnr":
                if source_col and source_col in self.source_df.columns:
                    for row_idx, val in self.source_df[source_col].items():
                        if pd.notna(val) and str(val).strip():
                            cleaned_kvnr = str(val).strip().upper()
                            if not validate_insurance_number(cleaned_kvnr):
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
                    
            elif rule_type == "validate_email":
                if source_col and source_col in self.source_df.columns:
                    for row_idx, val in self.source_df[source_col].items():
                        if pd.notna(val) and str(val).strip():
                            cleaned_email = str(val).strip()
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

            # Automatische Regel-Zuordnungen, falls keine explizite Regel gewählt wurde
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

            if rule_type == "copy_target":
                copy_rules[target_col] = rule.get('param')
                continue
            
            # PASS 1: Transformationen pro Zielspalte durchführen
        for target_col, dtype in target_schema.items():
            rule = self.transformations.get(target_col, {})
            
            # --- NEU: rule_type UND param HIER VORAB DEFINIEREN ---
            if isinstance(rule, dict):
                rule_type = rule.get('type')
                param = rule.get('param')
            elif isinstance(rule, str):
                rule_type = rule
                param = None
            else:
                rule_type = None
                param = None

            # Quellspalte aus dem Dropdown holen
            source_col = self.mapping_dropdowns[target_col].get() if target_col in self.mapping_dropdowns else None

            # --- 1. PLZ aus Ortsnamen ermitteln ---
            if rule_type == "lookup_plz_by_city":
                city_source_col = param if (param and param in self.source_df.columns) else source_col
                
                def fill_plz(row):
                    # 1. Bestehende PLZ aus Quellspalte holen (falls zugeordnet)
                    val = row[source_col] if (source_col and source_col in self.source_df.columns) else None
                    if pd.notna(val) and str(val).strip():
                        return str(val).strip().zfill(5)
                    
                    # 2. Falls leer: Versuchen PLZ aus Ort zu ermitteln
                    if city_source_col and city_source_col in self.source_df.columns:
                        city_val = row[city_source_col]
                        if pd.notna(city_val) and str(city_val).strip():
                            found_plz = self.plz_service.get_plz_by_city(str(city_val))
                            if found_plz:
                                return found_plz
                    return default_empty_value

                out_df[target_col] = self.source_df.apply(fill_plz, axis=1)

            # --- 2. Ort aus PLZ ermitteln ---
            elif rule_type == "lookup_city_by_plz":
                plz_source_col = param if (param and param in self.source_df.columns) else source_col

                def fill_city(row):
                    # 1. Bestehenden Ort aus Quellspalte holen (falls zugeordnet)
                    val = row[source_col] if (source_col and source_col in self.source_df.columns) else None
                    if pd.notna(val) and str(val).strip():
                        return str(val).strip()

                    # 2. Falls leer: Versuchen Ort aus PLZ zu ermitteln
                    if plz_source_col and plz_source_col in self.source_df.columns:
                        plz_val = row[plz_source_col]
                        if pd.notna(plz_val) and str(plz_val).strip():
                            found_city = self.plz_service.get_city_by_plz(str(plz_val))
                            if found_city:
                                return found_city
                    return default_empty_value

                out_df[target_col] = self.source_df.apply(fill_city, axis=1)

            # --- 3. Krankenkasse aus IK ermitteln ---
            elif rule_type == "lookup_ik_provider":
                ik_source_col = param if (param and param in self.source_df.columns) else source_col
                
                if ik_source_col and ik_source_col in self.source_df.columns:
                    # Fallback auf Haupt-App-Instanz sicherstellen
                    ik_service = getattr(self, 'ik_service', None)

                    def resolve_ik(val):
                        if pd.isna(val) or not str(val).strip():
                            return default_empty_value
                        
                        cleaned_ik = str(val).strip().split('.')[0] # z. B. 109777509.0 -> 109777509
                        
                        if ik_service:
                            provider_name = ik_service.get_provider_by_ik(cleaned_ik)
                            return provider_name if provider_name else default_empty_value
                        return default_empty_value

                    out_df[target_col] = self.source_df[ik_source_col].apply(resolve_ik)
                else:
                    out_df[target_col] = default_empty_value
                    
            # --- Validierung IK-Nummer ---
            elif rule_type == "validate_ik":
                if source_col and source_col in self.source_df.columns:
                    def check_ik_val(val):
                        if pd.isna(val) or not str(val).strip():
                            return default_empty_value
                        cleaned_ik = str(val).strip().split('.')[0].zfill(9)
                        # Gibt den Wert zurück, wenn gültig; ansonsten default_empty_value (oder z.B. Invalid-Marker)
                        return cleaned_ik if validate_ik_number(cleaned_ik) else default_empty_value

                    out_df[target_col] = self.source_df[source_col].apply(check_ik_val)
                else:
                    out_df[target_col] = default_empty_value

            # --- Validierung Versichertennummer (KVNR) ---
            elif rule_type == "validate_kvnr":
                if source_col and source_col in self.source_df.columns:
                    def check_kvnr_val(val):
                        if pd.isna(val) or not str(val).strip():
                            return default_empty_value
                        cleaned_kvnr = str(val).strip().upper()
                        return cleaned_kvnr if validate_insurance_number(cleaned_kvnr) else default_empty_value

                    out_df[target_col] = self.source_df[source_col].apply(check_kvnr_val)
                else:
                    out_df[target_col] = default_empty_value
                    
            elif rule_type == "validate_email":
                if source_col and source_col in self.source_df.columns:
                    def check_email_val(val):
                        if pd.isna(val) or not str(val).strip():
                            return default_empty_value
                        cleaned_email = str(val).strip()
                        return cleaned_email if validate_email(cleaned_email) else default_empty_value

                    out_df[target_col] = self.source_df[source_col].apply(check_email_val)
                else:
                    out_df[target_col] = default_empty_value
            
            elif rule_type == "static_value":
                static_val = str(rule.get('param', ''))
                out_df[target_col] = static_val
                if source_col != "-- Nicht zuordnen / Spezielle Regel --":
                    mapped_source_cols.add(source_col)

            elif rule_type == "generate_uid":
                out_df[target_col] = [generate_id() for _ in range(row_count)]
                if source_col != "-- Nicht zuordnen / Spezielle Regel --":
                    mapped_source_cols.add(source_col)

            elif source_col != "-- Nicht zuordnen / Spezielle Regel --":
                mapped_source_cols.add(source_col)
                series = self.source_df[source_col].copy()

                # 1. Grundlegende String-Bereinigung auf Textspalten anwenden
                is_email = rule_type == "validate_email" or any(k in target_col.lower() for k in ['email', 'mail'])
                is_city = any(k in target_col.lower() for k in ['ort', 'city', 'stadt'])
                is_name = any(k in target_col.lower() for k in ['name', 'vname'])
                
                if is_email:
                    # E-Mails: Nur trimmen
                    series = series.astype(str).apply(lambda x: x.strip() if pd.notna(x) else "")
                elif is_city:
                    # Ortsnamen: Normalisieren, aber Sonderzeichen-Filter deaktivieren (Klammern/Slashes behalten)
                    series = series.astype(str).apply(lambda x: sanitize_data_string(x, remove_special_chars=False))
                else:
                    # Restliche Namensfelder
                    series = series.astype(str).apply(lambda x: sanitize_data_string(x, remove_special_chars=is_name))

                # 2. Transformationsregeln anwenden
                if rule_type == "format_date" or 'birth' in target_col.lower() or 'datum' in target_col.lower():
                    date_fallback = str(rule.get('param', '')).strip() if rule.get('param') else ""
                    if date_fallback:
                        series = series.apply(lambda x: date_fallback if pd.isna(x) or str(x).strip() in ['', 'nan', 'null', 'None'] else x)
                    series = series.apply(format_date_iso)

                elif rule_type == "default_value":
                    fallback_val = str(rule.get('param', ''))
                    series = series.apply(lambda x: fallback_val if pd.isna(x) or str(x).strip() in ['', 'nan', 'null', 'None'] else x)

                elif rule_type == "clean_plz":
                    def format_plz(val):
                        val_str = str(val).strip() if pd.notna(val) else ""
                        if not val_str or val_str.lower() in ['nan', 'null', 'none', '']:
                            return ""
                        cleaned = re.sub(r'\.0$', '', val_str)
                        if cleaned.isdigit() and len(cleaned) <= 5:
                            return cleaned.zfill(5)
                        return cleaned
                    series = series.apply(format_plz)

                elif rule_type == "gender":
                    mapping_dict = {
                        "M": "Herr", "m": "Herr", "HERR": "Herr", "Herr": "Herr", "männlich": "Herr", "1": "Herr",
                        "W": "Frau", "w": "Frau", "FRAU": "Frau", "Frau": "Frau", "weiblich": "Frau", "F": "Frau", "f": "Frau", "2": "Frau"
                    }
                    series = series.apply(lambda x: mapping_dict.get(str(x).strip(), str(x).strip() if str(x).strip() else default_empty_value))

                elif rule_type == "split_street":
                    def get_street_name(val):
                        if pd.isna(val) or str(val).lower() in ['nan', 'null', 'none', '']:
                            return ""
                        return re.sub(r'\s*\d+.*$', '', str(val)).strip()
                    series = series.apply(get_street_name)

                elif rule_type == "split_number":
                    def get_house_number(val):
                        if pd.isna(val) or str(val).lower() in ['nan', 'null', 'none', '']:
                            return ""
                        numbers = re.findall(r'\d+.*$', str(val))
                        return "".join(numbers).strip() if numbers else ""
                    series = series.apply(get_house_number)

                elif rule_type == "merge_columns":
                    second_col = rule.get('param')
                    if second_col and second_col in self.source_df.columns:
                        mapped_source_cols.add(second_col)
                        s2 = self.source_df[second_col].astype(str).apply(
                            lambda x: sanitize_data_string(x, remove_special_chars=is_name_or_city)
                        )
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
            dialog = ValidationFixDialog(self, invalid_records)
            self.wait_window(dialog)  # Warten bis Dialog geschlossen wurde

            if not dialog.is_accepted:
                # Abbrechen geklickt / Fenster geschlossen -> Export abbrechen
                return

            # Entscheidungen des Benutzers in out_df anwenden
            for item in invalid_records:
                r_idx = item['row_idx']
                col = item['target_col']
                action = item['action']

                if action == 'clear':
                    out_df.at[r_idx, col] = default_empty_value
                elif action == 'custom':
                    out_df.at[r_idx, col] = item['custom_val'] if item['custom_val'] else default_empty_value
                # Bei 'keep' bleibt der original ausgeleSubst/Rohwert im DataFrame erhalten
        
        for target_col, source_target_col in copy_rules.items():
            if source_target_col in out_df.columns:
                out_df[target_col] = out_df[source_target_col].copy()
            else:
                out_df[target_col] = default_empty_value

        out_df = out_df[list(target_schema.keys())]

        # PASS 3: Überlängen-Erfassung
        conflicts = []
        for target_col, dtype_str in target_schema.items():
            limit = parse_varchar_limit(dtype_str)
            if limit:
                for r_idx, val in enumerate(out_df[target_col]):
                    val_str = str(val)
                    if val_str != "NULL" and pd.notna(val) and len(val_str) > limit:
                        conflicts.append({
                            'row_idx': r_idx,
                            'col_name': target_col,
                            'limit': limit,
                            'orig_val': val_str
                        })

        if conflicts:
            val_dialog = RowValidationDialog(self, conflicts)
            self.wait_window(val_dialog)
            
            if not val_dialog.confirmed:
                return

            resolved_items = val_dialog.get_resolved_values()
            for res in resolved_items:
                out_df.at[res['row_idx'], res['col_name']] = res['new_val']

        all_source_cols = set(self.source_df.columns)
        unmapped_cols = list(all_source_cols - mapped_source_cols)
        unmapped_df = self.source_df[unmapped_cols] if unmapped_cols else pd.DataFrame()
        
        used_source_cols = set()
        for target_col, dropdown in self.mapping_dropdowns.items():
            val = dropdown.get()
            if val and val != "-- Nicht zuordnen / Spezielle Regel --":
                used_source_cols.add(val)

        # Ebenfalls Spalten berücksichtigen, die in Transformations-Parametern verwendet wurden
        for rule in self.transformations.values():
            if isinstance(rule, dict) and rule.get('param'):
                used_source_cols.add(rule['param'])

        unmapped_source_cols = [c for c in self.source_df.columns if c not in used_source_cols]

        extra_fields_mappings = []
        if unmapped_source_cols and self.combo_schema.get() == "patienten":
            extra_dialog = ExtraFieldsDialog(self, unmapped_source_cols)
            self.wait_window(extra_dialog)

            if extra_dialog.is_accepted:
                extra_fields_mappings = extra_dialog.result_mappings

        # --- 4. EXPORT DER HAUPT- UND ZUSATZDATEIEN ---
        # Basis-Dateipfad vom Nutzer abfragen oder automatisch generieren
        export_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dateien", "*.csv"), ("Excel Dateien", "*.xlsx")]
        )

        if not export_path:
            return  # Abgebrochen
        
        if extra_fields_mappings:
            # A) Eigenschafts-Definitionen: pat_property.csv
            property_rows = []
            for item in extra_fields_mappings:
                # DB-Bezeichner sicherstellen (immer mit führendem '#')
                raw_name = item['field_name'].lstrip('#')
                property_id = f"#{raw_name}"
                
                property_rows.append({
                    'id': property_id,              # z. B. "#hausarzt_tel"
                    'label': item['source_col'],    # GUI-Labeltext aus CSV
                    'proptyp': item['data_type'],   # z. B. "TXT"
                    'options': "NULL",                # NULL
                    'maxwidth': 255,                # Festwert 255
                    'bereich': "NULL",                # NULL
                    'sortierung': 0,                # Festwert 0
                    'system': 202,                  # Festwert 202
                    'kartei_id': "NULL"               # NULL
                })
            
            df_pat_property = pd.DataFrame(property_rows)

            # B) Werte-Zuordnung: pat_property_map.csv
            # Patient-ID ermitteln
            patient_ids = out_df['id'] if 'id' in out_df.columns else self.source_df.index

            map_rows = []
            for item in extra_fields_mappings:
                raw_name = item['field_name'].lstrip('#')
                property_id = f"#{raw_name}"
                src_col = item['source_col']

                # Für jeden Patienten mit vorhandenem Wert einen Eintrag mit eigener UID erzeugen
                for p_id, raw_val in zip(patient_ids, self.source_df[src_col]):
                    if pd.notna(raw_val) and str(raw_val).strip() != "":
                        map_rows.append({
                            'id': str(generate_id()),      # Eigene selbstgenerierte UID
                            'property_id': property_id,   # Referenz mit # (z. B. "#hausarzt_tel")
                            'patienten_id': p_id,         # Referenz auf die Patienten-ID
                            'content': str(raw_val).strip() # Eigentlicher Wert
                        })

            df_pat_property_map = pd.DataFrame(map_rows)


            # --- 5. EXPORT DER ZUSATZDATEIEN ---
            # Erzeugt 'pat_property.csv' und 'pat_property_map.csv' im selben Ordner wie die Hauptdatei
            output_dir = os.path.dirname(export_path)

            path_property = os.path.join(output_dir, "pat_property.csv")
            path_property_map = os.path.join(output_dir, "pat_property_map.csv")

            df_pat_property.to_csv(path_property, index=False, sep=";", encoding="utf-8-sig")
            df_pat_property_map.to_csv(path_property_map, index=False, sep=";", encoding="utf-8-sig")

        base_path, ext = os.path.splitext(export_path)

        # 1. Haupt-Tabelle exportieren (z.B. patienten.csv)
        if ext.lower() == ".xlsx":
            with pd.ExcelWriter(export_path) as writer:
                out_df.to_excel(writer, sheet_name="Patienten", index=False)
        else:
            # CSV-Export (Separat mit Präfixen für die Zusatztabellen)
            out_df.to_csv(export_path, index=False, sep=";", encoding="utf-8-sig")
            
        if self.combo_schema.get() == "patienten":
            messagebox.showinfo("Export erfolgreich", "Die Patientendaten sowie die Zusatzfelder-Tabellen wurden erfolgreich exportiert.")
        elif self.combo_schema.get() == "adressen":
                    messagebox.showinfo("Export erfolgreich", "Die Adressen wurden erfolgreich exportiert.")
        
if __name__ == "__main__":
    app = CSVMappingApp()
    app.mainloop()
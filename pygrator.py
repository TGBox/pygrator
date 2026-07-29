# type: ignore
import os
import re
import pandas as pd
import csv
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from db_util import format_date_iso, generate_id, parse_varchar_limit, sanitize_data_string
from schemas import SCHEMAS

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
    "lookup_ik_provider": "Krankenkasse aus IK"
}

# Farbschema & Theme für modernere Optik
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# DONE: TODO: Check and verify that the newly added assignments for default connections between columns has worked as intended.
# TODO: Add a way to automatically fill the insurance provider name from the ik number that is specified.
# TODO: Add validation for the values of the fields.
# TODO: Add a way to add the name of a city from its post code and vice versa. There might be a method like this already in the py-handelsregister repositry! CHECK THAT OUT!
# TODO: Add more comments to this file.
# TODO: Split this file into multiple parts.
# TODO: Add corrects type annotations to all files.
# TODO: Add rule for always copying the contents of "id" to "p_nr" or "ext_id" if these fields exist.
# TODO: Add a verification for the IK number. (Only format [explicitly only numerical with length 9] or maybe with proper check of the IK?) => Last part maybe not feasible because these IKs are always private therapists and not commonly known institutions!
# TODO: Add a verification for the insurance number. (one letter followed by 9 digits)
# TODO: Add a way to map the left over fields to the additional fields, if the target is a patients table.
# TODO: Add a method that can get turned on optionally in the gui. The method should list all field values that have been altered or that would be altered. Also with batch select and single select options on how to handle these entries.

def center_window(window, width: int, height: int):
    # Aktualisiert die Geometrie-Informationen des Fensters
    window.update_idletasks()
    
    # Bildschirmmaße ermitteln
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Position berechnen
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    
    # Geometrie setzen: "Breite x Höhe + X-Offset + Y-Offset"
    window.geometry(f"{width}x{height}+{x}+{y}")

class RowValidationDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, conflicts: list[str]):
        super().__init__(parent)
        self.title("⚠️ Individuelle Feldlängen-Konflikte lösen (Zellgenau)")
        center_window(self, 980, 730)
        self.grab_set()

        self.conflicts = conflicts
        self.rows_data = []
        self.resolved_results = []
        self.confirmed = False

        top_frame: ctk.CTkFrame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            top_frame, 
            text=f"Es wurden {len(conflicts)} überlange Einzelwerte gefunden.", 
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(5, 2))

        ctk.CTkLabel(
            top_frame, 
            text="Du kannst für jeden einzelnen Wert entscheiden oder oben Schnellaktionen für alle Werte anwenden:", 
            font=("Arial", 11),
            text_color="gray70"
        ).pack(anchor="w", padx=10, pady=(0, 5))

        global_bar = ctk.CTkFrame(self, fg_color="gray20")
        global_bar.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(global_bar, text="Massenaktion auf alle:", font=("Arial", 11, "bold")).pack(side="left", padx=10, pady=8)
        
        ctk.CTkButton(
            global_bar, 
            text="Alle automatisch kürzen", 
            width=150, 
            fg_color="gray35", 
            hover_color="gray45",
            command=self.bulk_truncate
        ).pack(side="left", padx=5, pady=8)

        ctk.CTkButton(
            global_bar, 
            text="Alle unverändert lassen", 
            width=150, 
            fg_color="gray35", 
            hover_color="gray45",
            command=self.bulk_ignore
        ).pack(side="left", padx=5, pady=8)

        self.scroll = ctk.CTkScrollableFrame(self, label_text="Betroffene Tabellenzellen")
        self.scroll.pack(fill="both", expand=True, padx=15, pady=10)

        for item in conflicts:
            row_idx = item['row_idx']
            col_name = item['col_name']
            limit = item['limit']
            orig_val = item['orig_val']
            orig_len = len(orig_val)

            card = ctk.CTkFrame(self.scroll)
            card.pack(fill="x", pady=5, padx=5)

            info_txt = f"Zeile {row_idx + 1} | Spalte: '{col_name}' | Max: VARCHAR({limit}) | Aktuell: {orig_len} Zeichen"
            lbl_info = ctk.CTkLabel(card, text=info_txt, font=("Arial", 11, "bold"), text_color="#E57373")
            lbl_info.pack(anchor="w", padx=10, pady=(5, 2))

            lbl_val = ctk.CTkLabel(card, text=f'Originaler Wert: "{orig_val}"', font=("Arial", 10), text_color="gray70")
            lbl_val.pack(anchor="w", padx=10, pady=(0, 5))

            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.pack(fill="x", padx=10, pady=(0, 8))

            var_action = ctk.StringVar(value="truncate")

            r_trunc = ctk.CTkRadioButton(
                action_frame, 
                text=f"Kürzen auf '{orig_val[:limit]}'", 
                variable=var_action, 
                value="truncate"
            )
            r_trunc.pack(side="left", padx=(0, 15))

            r_custom = ctk.CTkRadioButton(
                action_frame, 
                text="Eigener Wert:", 
                variable=var_action, 
                value="custom"
            )
            r_custom.pack(side="left", padx=(0, 5))

            entry_custom = ctk.CTkEntry(action_frame, width=180, placeholder_text="Ersatzwert eingeben...")
            entry_custom.insert(0, orig_val[:limit])
            entry_custom.pack(side="left", padx=(0, 15))

            r_ignore = ctk.CTkRadioButton(
                action_frame, 
                text="Unverändert belassen", 
                variable=var_action, 
                value="ignore"
            )
            r_ignore.pack(side="left")

            self.rows_data.append({
                'row_idx': row_idx,
                'col_name': col_name,
                'limit': limit,
                'orig_val': orig_val,
                'var_action': var_action,
                'entry_custom': entry_custom
            })

        bottom_bar = ctk.CTkFrame(self)
        bottom_bar.pack(fill="x", padx=15, pady=10)

        btn_apply = ctk.CTkButton(
            bottom_bar, 
            text="Entscheidungen anwenden & Exportieren", 
            fg_color="green", 
            hover_color="darkgreen",
            font=("Arial", 12, "bold"),
            command=self.on_apply
        )
        btn_apply.pack(side="right", padx=10, pady=10)

        btn_cancel = ctk.CTkButton(
            bottom_bar, 
            text="Abbrechen", 
            fg_color="gray30", 
            hover_color="gray40",
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=5, pady=10)

    def bulk_truncate(self):
        for r in self.rows_data:
            r['var_action'].set("truncate")

    def bulk_ignore(self):
        for r in self.rows_data:
            r['var_action'].set("ignore")

    def on_apply(self):
        self.resolved_results = []
        for r in self.rows_data:
            action = r['var_action'].get()
            if action == "truncate":
                final_val = r['orig_val'][:r['limit']]
            elif action == "custom":
                final_val = r['entry_custom'].get()
            else:
                final_val = r['orig_val']

            self.resolved_results.append({
                'row_idx': r['row_idx'],
                'col_name': r['col_name'],
                'new_val': final_val
            })

        self.confirmed = True
        self.destroy()

    def get_resolved_values(self):
        return self.resolved_results

class CSVMappingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CSV Data Mapper & Schema Validator")
        center_window(self, 1040, 880)

        self.source_df = None
        self.source_file_path = ""
        self.transformations = {}  
        self.mapping_dropdowns = {}

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

        self.chk_export_unmapped = ctk.CTkCheckBox(
            chk_frame, 
            text="Rest-Datei für ungemappte Spalten erstellen"
        )
        self.chk_export_unmapped.pack(anchor="w", pady=3)
        self.chk_export_unmapped.select()

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
            command=self.process_and_export
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
            
            # --- 1. Quellspalte automatisch matchen ---
            for src_col in self.source_df.columns:
                # Matches on exact identity.
                if src_col.lower() in target_col.lower() or target_col.lower() in src_col.lower():
                    combo.set(src_col)
                    break
                # Matches name1/title field. schema: adressen.
                if src_col.lower() == "titel" and "name1" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches name2/first name field. schema: adressen.
                if src_col.lower() == "vorname" and "name2" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches name3/last name field. schema: adressen.
                if src_col.lower() == "nachname" and "name3" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches first name field. schema: patienten.
                if src_col.lower() == "vorname" and "p_vname" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches last name field. schema: patienten.
                if src_col.lower() == "nachname" and "p_name" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches city field. schema: patienten.
                if src_col.lower() == "wohnort" and "p_ort" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches birthday field. schema: patienten.
                if src_col.lower() == "geburtsdatum" and "p_birth" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches gender field. schema: adressen.
                if src_col.lower() == "geschlecht" and "anrede" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches gender field. schema: patienten.
                if src_col.lower() == "geschlecht" and "p_anrede" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches telephone field. schema: patienten.
                if src_col.lower() == "telefon" and "p_tel" == target_col.lower():
                    combo.set(src_col)
                    break
                # Matches telephone2/telge field. schema: patienten.
                if src_col.lower() == "telefon2" and "p_telge" == target_col.lower():
                    combo.set(src_col)
                    break
                # Matches mobile phone field. schema: patienten.
                if src_col.lower() == "mobil" and "p_handy" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches mobile phone field. schema: adressen.
                if src_col.lower() == "telefonmobil" and "mobil" == target_col.lower():
                    combo.set(src_col)
                    break
                # Matches street field. schema: patienten.
                if src_col.lower() in ("strasse", "straße") and "p_street" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches house number field. schema: patienten.
                if src_col.lower() in ("strasse", "straße") and "p_hausnummer" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches IK field. schema: patienten.
                if src_col.lower() == "kas_ik" and "p_ik" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches insurance status field. schema: patienten.
                if src_col.lower() == "status" and "p_vs" in target_col.lower():
                    combo.set(src_col)
                    break
                # Matches insurance number field. schema: patienten.
                if src_col.lower() == "versichertennummer" and "p_vnr" in target_col.lower():
                    combo.set(src_col)
                    break

            self.mapping_dropdowns[target_col] = combo

            # --- 2. Automatische Voreinstellung von Regeln im Dict ---
            if target_col not in self.transformations:
                if target_col == "id":
                    self.transformations[target_col] = {'type': 'generate_uid'}
                elif "birth" in target_col:
                    self.transformations[target_col] = {'type': 'format_date'}
                elif "anrede" in target_col:
                    self.transformations[target_col] = {'type': 'gender'}
                elif "plz" in target_col:
                    self.transformations[target_col] = {'type': 'clean_plz'}
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
                button_text = f"✓ {rule_title} ({param})"
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
        center_window(dialog, 540, 750)
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

        r_plz = ctk.CTkRadioButton(dialog, text="📮 PLZ bereinigen (.0 entfernen & 5 Stellen)", variable=rule_type, value="clean_plz")
        r_plz.pack(anchor="w", padx=20, pady=5)

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

        # PASS 1: Transformationen
        for target_col, dtype_str in target_schema.items():
            source_col = self.mapping_dropdowns[target_col].get()
            rule = self.transformations.get(target_col, {})
            rule_type = rule.get('type')

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
            
            elif rule_type == "lookup_ik_provider":
                ik_source_col = rule.get('param')
                
                # Falls keine explizite IK-Spalte im Dialog gewählt wurde, 
                # schauen wir, ob die Zielspalte im Dropdown gemappt war.
                if (not ik_source_col or ik_source_col == "-- Nicht zuordnen / Spezielle Regel --") and source_col != "-- Nicht zuordnen / Spezielle Regel --":
                    ik_source_col = source_col

                if ik_source_col and ik_source_col in self.source_df.columns:
                    mapped_source_cols.add(ik_source_col)
                    
                    # Einmalige Instanziierung des IK Services (z.B. aus ik_lookup.py)
                    if not hasattr(self, 'ik_service'):
                        from ik_lookup import IKLookupService
                        self.ik_service = IKLookupService()
                    
                    def resolve_ik(val):
                        if pd.isna(val) or not str(val).strip():
                            return default_empty_value
                        cleaned_ik = str(val).strip().split('.')[0] # .0 bei Fließkommazahlen entfernen
                        provider_name = self.ik_service.get_provider_by_ik(cleaned_ik)
                        return provider_name if provider_name else default_empty_value

                    out_df[target_col] = self.source_df[ik_source_col].apply(resolve_ik)
                else:
                    out_df[target_col] = default_empty_value

            if rule_type == "static_value":
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

                # 1. Grundlegende String-Bereinigung auf ALLE Textspalten anwenden
                is_name_or_city = any(k in target_col.lower() for k in ['name', 'vname', 'ort', 'city', 'stadt'])
                
                # astype(str) garantiert saubere Strings für die Bereinigungsfunktion
                series = series.astype(str).apply(lambda x: sanitize_data_string(x, remove_special_chars=is_name_or_city))

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

        # PASS 2: Copy Rules
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

        # PASS 4: EXPORT NACH FORMAT UND ENCODING
        format_choice = self.combo_export_format.get()
        raw_encoding = self.combo_encoding.get().split()[0]  # Extrahiert z.B. 'utf-8-sig'

        if "Excel" in format_choice:
            file_ext = ".xlsx"
            file_types = [("Excel Workbook", "*.xlsx")]
        else:
            file_ext = ".csv"
            file_types = [("CSV Files", "*.csv")]

        save_path = filedialog.asksaveasfilename(
            defaultextension=file_ext,
            filetypes=file_types,
            initialfile=f"patienten{file_ext}"
        )

        if save_path:
            try:
                if "Excel" in format_choice:
                    out_df.to_excel(save_path, index=False)
                else:
                    sep_char = ';' if ';' in format_choice else ','
                    out_df.to_csv(save_path, index=False, encoding=raw_encoding, sep=sep_char)

                msg_rest = ""
                if self.chk_export_unmapped.get() and not unmapped_df.empty:
                    dir_name, file_name = os.path.split(save_path)
                    rest_file_path = os.path.join(dir_name, f"REST_UNMAPPED_{file_name}")
                    
                    if "Excel" in format_choice:
                        unmapped_df.to_excel(rest_file_path, index=False)
                    else:
                        sep_char = ';' if ';' in format_choice else ','
                        unmapped_df.to_csv(rest_file_path, index=False, encoding=raw_encoding, sep=sep_char)

                    msg_rest = f"\n\nUngemappte Spalten gesichert in:\n{os.path.basename(rest_file_path)}"

                messagebox.showinfo("Erfolg!", f"Datei erfolgreich exportiert!\nFormat: {format_choice}\nEncoding: {raw_encoding}{msg_rest}")

            except Exception as e:
                messagebox.showerror("Export-Fehler", f"Fehler beim Speichern der Datei:\n{str(e)}")

if __name__ == "__main__":
    app = CSVMappingApp()
    app.mainloop()
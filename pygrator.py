# type: ignore
import os
import re
import pandas as pd
import csv
import customtkinter as ctk
from tkinter import filedialog, messagebox

from db_util import generate_id
from schemas import SCHEMAS

# Farbschema & Theme für modernere Optik
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def parse_varchar_limit(datatype_str: str) -> int | None:
    """Extrahiert das Limit aus einem Typ-String wie 'VARCHAR(40)' -> 40. Bei 'TEXT' -> None."""
    match = re.search(r'VARCHAR\((\d+)\)', str(datatype_str), re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def format_date_iso(val) -> str:
    """Wandelt Datumsangaben (z.B. '15.08.1985', '1985/08/15', '15.8.85') sauber in 'YYYY-MM-DD' um."""
    if pd.isna(val):
        return ""
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['nan', 'null', 'none', '']:
        return ""

    # Falls bereits YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', val_str):
        return val_str

    try:
        # Versuch per Pandas to_datetime mit automatischer/deutscher Formaterkennung
        parsed_dt = pd.to_datetime(val_str, dayfirst=True, errors='coerce')
        if pd.notna(parsed_dt):
            return parsed_dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    return val_str

class RowValidationDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, conflicts: list[str]):
        super().__init__(parent)
        self.title("⚠️ Individuelle Feldlängen-Konflikte lösen (Zellgenau)")
        self.geometry("980x680")
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
        self.geometry("1040x820")

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

        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=15, pady=10)

        chk_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        chk_frame.pack(side="left", padx=10, pady=5)

        self.chk_fill_null = ctk.CTkCheckBox(
            chk_frame, 
            text="Unbelegte Felder mit 'NULL' auffüllen (statt leerem Text)"
        )
        self.chk_fill_null.pack(anchor="w", pady=3)

        self.chk_export_unmapped = ctk.CTkCheckBox(
            chk_frame, 
            text="Rest-Datei für ungemappte Spalten erstellen"
        )
        self.chk_export_unmapped.pack(anchor="w", pady=3)
        self.chk_export_unmapped.select()
        self.chk_fill_null.select()

        ctk.CTkButton(
            bottom_frame, 
            text="Prüfen & Exportieren", 
            fg_color="green", 
            hover_color="darkgreen",
            command=self.process_and_export
        ).pack(side="right", padx=10, pady=10)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")])
        if not file_path:
            return

        detected_sep = ';'
        try:
            with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                sample = f.read(4096)
                sniffer = csv.Sniffer()
                detected_sep = sniffer.sniff(sample).delimiter
        except Exception:
            pass

        encodings_to_try = ['utf-8-sig', 'utf-8', 'cp1252', 'latin1']
        loaded_df = None
        used_encoding = ""

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
            messagebox.showerror("Fehler beim Laden", "Konnte die Datei mit keinem gängigen Encoding lesen.")

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

        for idx, (target_col, dtype) in enumerate(target_schema.items(), start=1):
            label_text = f"{target_col} ({dtype})"
            ctk.CTkLabel(self.scroll_frame, text=label_text, font=("Consolas", 11)).grid(row=idx, column=0, padx=10, pady=5, sticky="w")

            combo = ctk.CTkOptionMenu(self.scroll_frame, values=source_cols)
            combo.grid(row=idx, column=1, padx=10, pady=5, sticky="w")
            
            for col in self.source_df.columns:
                if col.lower() in target_col.lower() or target_col.lower() in col.lower():
                    combo.set(col)
                    break

            self.mapping_dropdowns[target_col] = combo

            btn_trans = ctk.CTkButton(
                self.scroll_frame, 
                text="Regel hinzufügen...", 
                width=160,
                fg_color="gray30",
                command=lambda t=target_col: self.open_transformation_dialog(t)
            )
            btn_trans.grid(row=idx, column=2, padx=10, pady=5, sticky="w")

    def open_transformation_dialog(self, target_col):
        target_schema = SCHEMAS[self.combo_schema.get()]
        other_target_cols = [col for col in target_schema.keys() if col != target_col]

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Transformation für '{target_col}'")
        dialog.geometry("540x650")
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

        current_type = existing_rule.get('type', default_rule)
        rule_type = ctk.StringVar(value=current_type)

        r0 = ctk.CTkRadioButton(dialog, text="🔑 Neue UID generieren (Kompakt)", variable=rule_type, value="generate_uid")
        r0.pack(anchor="w", padx=20, pady=5)

        # 📅 DATUMSFORMATIERUNG MIT NEUEM STANDARDWERT-FELD
        r_date = ctk.CTkRadioButton(dialog, text="📅 Datumsformat anpassen -> YYYY-MM-DD", variable=rule_type, value="format_date")
        r_date.pack(anchor="w", padx=20, pady=5)

        date_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        date_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(date_frame, text="Standardwert bei leeren Feldern (optional):", font=("Arial", 10), text_color="gray70").pack(side="left", padx=5)
        entry_date_default = ctk.CTkEntry(date_frame, width=160, placeholder_text="z. B. 1900-01-01")
        entry_date_default.pack(side="left")
        if existing_rule.get('type') == 'format_date' and existing_rule.get('param'):
            entry_date_default.insert(0, str(existing_rule.get('param')))

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

        r_copy = ctk.CTkRadioButton(dialog, text="🔗 Wert aus anderer Zielspalte übernehmen", variable=rule_type, value="copy_target")
        r_copy.pack(anchor="w", padx=20, pady=5)

        copy_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        copy_frame.pack(anchor="w", padx=45, pady=2)
        ctk.CTkLabel(copy_frame, text="Kopieren aus:").pack(side="left", padx=5)
        combo_copy_target = ctk.CTkOptionMenu(copy_frame, values=other_target_cols if other_target_cols else ["Keine"])
        combo_copy_target.pack(side="left")
        if existing_rule.get('type') == 'copy_target' and existing_rule.get('param') in other_target_cols:
            combo_copy_target.set(existing_rule.get('param'))

        r_plz = ctk.CTkRadioButton(dialog, text="📮 PLZ bereinigen (.0 entfernen & 5 Stellen)", variable=rule_type, value="clean_plz")
        r_plz.pack(anchor="w", padx=20, pady=5)

        r1 = ctk.CTkRadioButton(dialog, text="👫 Geschlecht mappen (M->Herr, W->Frau)", variable=rule_type, value="gender")
        r1.pack(anchor="w", padx=20, pady=5)

        r2 = ctk.CTkRadioButton(dialog, text="🏠 Straße/Hausnr. trennen -> Nur Text", variable=rule_type, value="split_street")
        r2.pack(anchor="w", padx=20, pady=5)

        r3 = ctk.CTkRadioButton(dialog, text="🔢 Straße/Hausnr. trennen -> Nur Nummer", variable=rule_type, value="split_number")
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

            if t_type == "merge_columns":
                param = combo_merge_source.get()
            elif t_type == "copy_target":
                param = combo_copy_target.get()
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
            messagebox.showinfo("Gespeichert", f"Regel '{t_type}' für '{target_col}' hinterlegt.")
            dialog.destroy()

        def remove_rule():
            if target_col in self.transformations:
                del self.transformations[target_col]
            messagebox.showinfo("Entfernt", f"Keine Regel mehr für '{target_col}' aktiv.")
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="Speichern", command=save_rule).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Regel löschen", fg_color="red3", hover_color="red4", command=remove_rule).pack(side="left", padx=5)

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

        # PASS 1: Reguläre Transformationen
        for target_col, dtype_str in target_schema.items():
            source_col = self.mapping_dropdowns[target_col].get()
            rule = self.transformations.get(target_col, {})
            rule_type = rule.get('type')

            if not rule_type:
                if 'birth' in target_col.lower() or 'datum' in target_col.lower() or target_col.endswith('_bis'):
                    rule_type = 'format_date'
                elif 'plz' in target_col.lower():
                    rule_type = 'clean_plz'

            if rule_type == "copy_target":
                copy_rules[target_col] = rule.get('param')
                continue

            if rule_type == "static_value":
                static_val = str(rule.get('param', ''))
                out_df[target_col] = static_val
                if source_col != "-- Nicht zuordnen / Spezielle Regel --":
                    mapped_source_cols.add(source_col)

            elif rule_type == "generate_uid":
                out_df[target_col] = [generate_id() for _ in range(row_count)]
                if source_col != "-- Nicht zuordnen / Spezielle Regel --":
                    mapped_source_cols.add(source_col)
                    
            elif rule_type == "merge_columns":
                second_source = rule.get('param')
                
                # Beide Quellspalten als gemappt markieren
                if source_col != "-- Nicht zuordnen / Spezielle Regel --":
                    mapped_source_cols.add(source_col)
                if second_source and second_source in self.source_df.columns:
                    mapped_source_cols.add(second_source)

                # Werte aus beiden Spalten holen und säubern
                val1 = self.source_df[source_col].fillna("").astype(str).str.strip() if source_col in self.source_df.columns else pd.Series([""] * row_count)
                val2 = self.source_df[second_source].fillna("").astype(str).str.strip() if second_source and second_source in self.source_df.columns else pd.Series([""] * row_count)

                # Mit Leerzeichen zusammenfügen (ohne führende/anhängende Leerzeichen bei leeren Feldern)
                merged_series = (val1 + " " + val2).str.strip()

                if self.chk_fill_null.get():
                    merged_series = merged_series.replace(r'^\s*$', "NULL", regex=True)

                out_df[target_col] = merged_series

            elif source_col != "-- Nicht zuordnen / Spezielle Regel --":
                mapped_source_cols.add(source_col)
                series = self.source_df[source_col].copy()

                # DATUMSFORMATIERUNG HIER MIT DEFAULT-WERT
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
                    mapping_dict = {"M": "Herr", "m": "Herr", "W": "Frau", "w": "Frau", "F": "Frau"}
                    series = series.map(mapping_dict).fillna(default_empty_value)

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

        # PASS 3: ZELLGENAUE ÜBERLÄNGEN-ERFASSUNG
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

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="patienten.csv"
        )

        if save_path:
            out_df.to_csv(save_path, index=False, encoding="utf-8", sep=";")

            msg_rest = ""
            if self.chk_export_unmapped.get():
                dir_name, file_name = os.path.split(save_path)
                rest_file_path = os.path.join(dir_name, f"REST_UNMAPPED_{file_name}")
                if not unmapped_df.empty:
                    unmapped_df.to_csv(rest_file_path, index=False, encoding="utf-8", sep=";")
                    msg_rest = f"\n\nUngemappte Spalten gesichert in:\n{os.path.basename(rest_file_path)}"

            messagebox.showinfo("Erfolg!", f"Datei erfolgreich verarbeitet!{msg_rest}")


if __name__ == "__main__":
    app = CSVMappingApp()
    app.mainloop()
# type: ignore
import customtkinter as ctk
from typing import List, Dict, Any

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

class ExtraFieldsDialog(ctk.CTkToplevel):
    def __init__(self, parent, unmapped_columns: List[str]):
        """
        unmapped_columns: Liste aller CSV-Quellspalten, die bisher keinem Zielschema-Feld zugeordnet wurden.
        """
        super().__init__(parent)
        self.parent = parent
        self.unmapped_columns = unmapped_columns
        self.result_mappings: List[Dict[str, str]] = []  # Liste der ausgewählten Zusatzfelder
        self.is_accepted = False

        self.title("⚙️ Zusatzfelder für ungemappte Spalten definieren")
        center_window(self, 800, 600)
        self.attributes("-topmost", True)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        # Header
        header_lbl = ctk.CTkLabel(
            self, 
            text="Unbenutzte Quellspalten als Zusatzfelder registrieren", 
            font=("Arial", 14, "bold")
        )
        header_lbl.pack(padx=15, pady=(15, 5), anchor="w")

        sub_lbl = ctk.CTkLabel(
            self, 
            text="Wähle Spalten aus, die in die Zusatzdaten-Tabellen übernommen werden sollen:", 
            font=("Arial", 11)
        )
        sub_lbl.pack(padx=15, pady=(0, 10), anchor="w")

        # Scrollbare Liste für alle ungemappten Spalten
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Nicht zugeordnete Quellspalten")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Spaltenköpfe in der Liste
        headers_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        headers_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(headers_frame, text="Übernehmen?", font=("Arial", 10, "bold"), width=90).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Quellspalte (CSV)", font=("Arial", 10, "bold"), width=180, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Zusatzfeld-Name (DB)", font=("Arial", 10, "bold"), width=200, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Datentyp", font=("Arial", 10, "bold"), width=120, anchor="w").pack(side="left", padx=5)

        self.row_widgets = []
        for idx, col_name in enumerate(self.unmapped_columns):
            self._render_column_row(col_name)

        # Footer
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=15, pady=15)

        btn_cancel = ctk.CTkButton(
            footer_frame, text="Überspringen", fg_color="gray40", 
            command=self.destroy
        )
        btn_cancel.pack(side="left")

        btn_apply = ctk.CTkButton(
            footer_frame, text="Zusatzfelder übernehmen & Exportieren", 
            fg_color="#1E7E34", hover_color="#145A24", font=("Arial", 12, "bold"),
            height=35, command=self._on_apply
        )
        btn_apply.pack(side="right")

    def _render_column_row(self, col_name: str):
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", padx=5, pady=3)

        # 1. Checkbox (Soll übernommen werden?)
        var_include = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(row_frame, text="", variable=var_include, width=30)
        chk.pack(side="left", padx=10)

        # 2. Quellspalten-Name
        lbl_src = ctk.CTkLabel(row_frame, text=col_name, font=("Roboto", 11, "bold"), width=180, anchor="w")
        lbl_src.pack(side="left", padx=5)

        # Bereinigten Vorschlag für den DB-Spaltennamen erzeugen
        default_db_name = col_name.lower().strip().replace(" ", "_").replace("-", "_")
        default_db_name = "".join(c for c in default_db_name if c.isalnum() or c == "_")

        # 3. Eingabefeld für DB-Feldnamen / Label
        entry_name = ctk.CTkEntry(row_frame, width=190)
        entry_name.insert(0, default_db_name)
        entry_name.pack(side="left", padx=5)

        # 4. Proptyp-Dropdown (TXT, NUM, DATE, BOOL)
        combo_proptyp = ctk.CTkOptionMenu(
            row_frame, 
            values=["TXT", "NUM", "DATE", "BOOL"],
            width=130
        )
        combo_proptyp.set("TXT")
        combo_proptyp.pack(side="left", padx=5)

        # --- Interaktivität erst definieren, WENN ALLE WIDGETS ERSTELLT WURDEN ---
        def toggle_inputs():
            state = "normal" if var_include.get() else "disabled"
            entry_name.configure(state=state)
            combo_proptyp.configure(state=state)

        # Event-Verknüpfung & Initialisierung
        chk.configure(command=toggle_inputs)
        toggle_inputs()  # Setzt den initialen Zustand auf "disabled"

        # Daten für _on_apply speichern
        self.row_widgets.append({
            'source_col': col_name,
            'var_include': var_include,
            'entry_name': entry_name,
            'combo_proptyp': combo_proptyp
        })

    def _on_apply(self):
        self.result_mappings = []
        for rw in self.row_widgets:
            if rw['var_include'].get():
                target_field_name = rw['entry_name'].get().strip()
                if not target_field_name:
                    target_field_name = rw['source_col']
                
                self.result_mappings.append({
                    'source_col': rw['source_col'],
                    'field_name': target_field_name,
                    'data_type': rw['combo_proptyp'].get()
                })

        self.is_accepted = True
        self.destroy()

class ValidationFixDialog(ctk.CTkToplevel):
    def __init__(self, parent, invalid_items: List[Dict[str, Any]]):
        """
        invalid_items ist eine Liste von Dictionaries:
        [
            {
                'row_idx': 0,
                'target_col': 'p_ik',
                'rule_type': 'validate_ik',
                'original_val': '12345',
                'action': 'keep', # 'keep', 'clear', 'custom'
                'custom_val': ''
            }, ...
        ]
        """
        super().__init__(parent)
        self.parent = parent
        self.invalid_items = invalid_items
        self.is_accepted = False

        self.title("⚠️ Validierungsfehler korrigieren")
        center_window(self, 850, 550)
        self.attributes("-topmost", True)
        self.grab_set()  # Modal machen

        # Erstelle Widgets
        self._build_ui()

    def _build_ui(self):
        # Header
        header_lbl = ctk.CTkLabel(
            self, 
            text=f"Es wurden {len(self.invalid_items)} ungültige Werte gefunden.", 
            font=("Arial", 14, "bold"),
            text_color="#FF6B6B"
        )
        header_lbl.pack(padx=15, pady=(15, 5), anchor="w")

        sub_lbl = ctk.CTkLabel(
            self, 
            text="Wähle eine globale Aktion oder korrigiere die Einträge einzeln:", 
            font=("Arial", 11)
        )
        sub_lbl.pack(padx=15, pady=(0, 10), anchor="w")

        # --- Frame für Globale Aktionen (Batch) ---
        batch_frame = ctk.CTkFrame(self)
        batch_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(batch_frame, text="Alle Eintrags-Aktionen:", font=("Arial", 11, "bold")).pack(side="left", padx=10, pady=10)
        
        btn_batch_keep = ctk.CTkButton(
            batch_frame, text="Alle beibehalten (Ignorieren)", fg_color="gray40", 
            command=lambda: self._apply_batch_action("keep")
        )
        btn_batch_keep.pack(side="left", padx=5, pady=10)

        btn_batch_clear = ctk.CTkButton(
            batch_frame, text="Alle leeren (NULL)", fg_color="#C0392B", 
            command=lambda: self._apply_batch_action("clear")
        )
        btn_batch_clear.pack(side="left", padx=5, pady=10)

        # --- Scrollbare Liste der einzelnen Fehler ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Fehlerhafte Einträge")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.row_widgets = []
        for idx, item in enumerate(self.invalid_items):
            self._render_item_row(idx, item)

        # --- Footer (Bestätigen) ---
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=15, pady=15)

        btn_apply = ctk.CTkButton(
            footer_frame, text="Änderungen übernehmen & Exportieren", 
            fg_color="#1E7E34", hover_color="#145A24", font=("Arial", 12, "bold"),
            height=35, command=self._on_apply
        )
        btn_apply.pack(side="right")

    def _render_item_row(self, idx: int, item: Dict[str, Any]):
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", padx=5, pady=5)

        # Info-Label (Zeile, Spalte, Fehler)
        rule_desc = "Ungültige IK" if item['rule_type'] == 'validate_ik' else "Ungültige KVNR"
        info_text = f"Zeile {item['row_idx'] + 1} | [{item['target_col']}] ({rule_desc}): '{item['original_val']}'"
        
        lbl = ctk.CTkLabel(row_frame, text=info_text, font=("Roboto", 11, "bold"), anchor="w", width=300)
        lbl.pack(side="left", padx=10, pady=5)

        # Variable für Radiobutton-Auswahl
        action_var = ctk.StringVar(value=item.get('action', 'keep'))

        # Manuelles Eingabefeld
        entry_custom = ctk.CTkEntry(row_frame, placeholder_text="Manuelle Korrektur", width=140)
        if item.get('custom_val'):
            entry_custom.insert(0, item['custom_val'])

        def on_action_change():
            if action_var.get() == "custom":
                entry_custom.configure(state="normal")
            else:
                entry_custom.configure(state="disabled")

        r_keep = ctk.CTkRadioButton(row_frame, text="Beibehalten", variable=action_var, value="keep", command=on_action_change, width=90)
        r_keep.pack(side="left", padx=5)

        r_clear = ctk.CTkRadioButton(row_frame, text="Leeren", variable=action_var, value="clear", command=on_action_change, width=70)
        r_clear.pack(side="left", padx=5)

        r_custom = ctk.CTkRadioButton(row_frame, text="Manuell:", variable=action_var, value="custom", command=on_action_change, width=80)
        r_custom.pack(side="left", padx=5)

        entry_custom.pack(side="left", padx=5)
        on_action_change()  # Initialen Zustand setzen

        self.row_widgets.append({
            'item': item,
            'action_var': action_var,
            'entry_custom': entry_custom
        })

    def _apply_batch_action(self, action: str):
        """Wendet 'keep' oder 'clear' auf alle Einträge an."""
        for rw in self.row_widgets:
            rw['action_var'].set(action)
            rw['entry_custom'].configure(state="disabled")

    def _on_apply(self):
        # Werte aus den UI-Elementen zurück ins item-Dict schreiben
        for rw in self.row_widgets:
            action = rw['action_var'].get()
            rw['item']['action'] = action
            rw['item']['custom_val'] = rw['entry_custom'].get().strip()

        self.is_accepted = True
        self.destroy()

import customtkinter as ctk
from typing import List, Dict, Any
from constants import *

def center_window(window: ctk.CTkToplevel, width: int, height: int) -> None:
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

class RowValidationDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, conflicts: List[Dict[str, Any]]):
        super().__init__(parent)
        self.title("⚠️ Individuelle Feldlängen-Konflikte lösen (Zellgenau)")
        center_window(self, ROW_VALIDATION_DIALOG_WIDTH, ROW_VALIDATION_DIALOG_HEIGHT)
        self.grab_set()

        self.conflicts = conflicts
        self.rows_data: List[Dict[str, Any]] = []
        self.resolved_results: List[Dict[str, Any]] = []
        self.confirmed = False

        top_frame: ctk.CTkFrame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=PADDING_L, pady=PADDING_M)

        ctk.CTkLabel(
            top_frame, 
            text=f"Es wurden {len(conflicts)} überlange Einzelwerte gefunden.", 
            font=LARGER_LABEL_FONT_BOLD
        ).pack(anchor="w", padx=PADDING_M, pady=(PADDING_XS, 2))

        ctk.CTkLabel(
            top_frame, 
            text="Du kannst für jeden einzelnen Wert entscheiden oder oben Schnellaktionen für alle Werte anwenden:", 
            font=LABEL_FONT,
            text_color=COL_GRAY_70
        ).pack(anchor="w", padx=PADDING_M, pady=(0, PADDING_XS))

        global_bar = ctk.CTkFrame(self, fg_color=COL_GRAY_20)
        global_bar.pack(fill="x", padx=PADDING_L, pady=PADDING_XS)

        ctk.CTkLabel(global_bar, text="Massenaktion auf alle:", font=LABEL_FONT_BOLD).pack(side="left", padx=PADDING_M, pady=PADDING_S)
        
        ctk.CTkButton(
            global_bar, 
            text="Alle automatisch kürzen", 
            width=BATCH_PROCESS_BUTTON_WIDTH, 
            fg_color=COL_GRAY_35, 
            hover_color=COL_GRAY_45,
            command=self.bulk_truncate
        ).pack(side="left", padx=PADDING_XS, pady=PADDING_S)

        ctk.CTkButton(
            global_bar, 
            text="Alle unverändert lassen", 
            width=BATCH_PROCESS_BUTTON_WIDTH, 
            fg_color=COL_GRAY_35, 
            hover_color=COL_GRAY_45,
            command=self.bulk_ignore
        ).pack(side="left", padx=PADDING_XS, pady=PADDING_S)

        self.scroll = ctk.CTkScrollableFrame(self, label_text="Betroffene Tabellenzellen")
        self.scroll.pack(fill="both", expand=True, padx=PADDING_L, pady=PADDING_M)

        for item in conflicts:
            row_idx: int = int(item['row_idx'])
            col_name: str = str(item['col_name'])
            limit: int = int(item['limit'])
            orig_val: str = str(item['orig_val'])
            orig_len = len(orig_val)

            card = ctk.CTkFrame(self.scroll)
            card.pack(fill="x", pady=PADDING_XS, padx=PADDING_XS)

            info_txt = f"Zeile {row_idx + 1} | Spalte: '{col_name}' | Max: VARCHAR({limit}) | Aktuell: {orig_len} Zeichen"
            lbl_info = ctk.CTkLabel(card, text=info_txt, font=LABEL_FONT_BOLD, text_color=COL_LIGHT_RED)
            lbl_info.pack(anchor="w", padx=PADDING_M, pady=(PADDING_XS, 2))

            lbl_val = ctk.CTkLabel(card, text=f'Originaler Wert: "{orig_val}"', font=SMALL_LABEL_FONT, text_color=COL_GRAY_70)
            lbl_val.pack(anchor="w", padx=PADDING_M, pady=(0, PADDING_XS))

            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.pack(fill="x", padx=PADDING_M, pady=(0, PADDING_S))

            var_action = ctk.StringVar(value="truncate")

            r_trunc = ctk.CTkRadioButton(
                action_frame, 
                text=f"Kürzen auf '{orig_val[:limit]}'", 
                variable=var_action, 
                value="truncate"
            )
            r_trunc.pack(side="left", padx=(0, PADDING_L))

            r_custom = ctk.CTkRadioButton(
                action_frame, 
                text="Eigener Wert:", 
                variable=var_action, 
                value="custom"
            )
            r_custom.pack(side="left", padx=(0, PADDING_XS))

            entry_custom = ctk.CTkEntry(action_frame, width=REPLACEMENT_INPUT_WIDTH, placeholder_text="Ersatzwert eingeben...")
            entry_custom.insert(0, orig_val[:limit])
            entry_custom.pack(side="left", padx=(0, PADDING_L))

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
        bottom_bar.pack(fill="x", padx=PADDING_L, pady=PADDING_M)

        btn_apply = ctk.CTkButton(
            bottom_bar, 
            text="Entscheidungen anwenden & Exportieren", 
            fg_color=COL_GREEN, 
            hover_color=COL_DARK_GREEN,
            font=BUTTON_FONT,
            command=self.on_apply
        )
        btn_apply.pack(side="right", padx=PADDING_M, pady=PADDING_M)

        btn_cancel = ctk.CTkButton(
            bottom_bar, 
            text="Abbrechen", 
            fg_color=COL_GRAY_30, 
            hover_color=COL_GRAY_40,
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=PADDING_XS, pady=PADDING_M)

    def bulk_truncate(self) -> None:
        for r in self.rows_data:
            r['var_action'].set("truncate")

    def bulk_ignore(self) -> None:
        for r in self.rows_data:
            r['var_action'].set("ignore")

    def on_apply(self) -> None:
        self.resolved_results = []
        for r in self.rows_data:
            action = r['var_action'].get()
            limit = int(r['limit'])
            orig_val = str(r['orig_val'])
            
            if action == "truncate":
                final_val = orig_val[:limit]
            elif action == "custom":
                final_val = r['entry_custom'].get()
            else:
                final_val = orig_val

            self.resolved_results.append({
                'row_idx': r['row_idx'],
                'col_name': r['col_name'],
                'new_val': final_val
            })

        self.confirmed = True
        self.destroy()

    def get_resolved_values(self) -> List[Dict[str, Any]]:
        return self.resolved_results

class ExtraFieldsDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, unmapped_columns: List[str]):
        super().__init__(parent)
        self.parent = parent
        self.unmapped_columns = unmapped_columns
        self.result_mappings: List[Dict[str, str]] = []
        self.is_accepted = False

        self.title("⚙️ Zusatzfelder für ungemappte Spalten definieren")
        center_window(self, EXTRA_FIELDS_DIALOG_WIDTH, EXTRA_FIELDS_DIALOG_HEIGHT)
        self.attributes("-topmost", True)  # pyright: ignore[reportUnknownMemberType]
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        # Header
        header_lbl = ctk.CTkLabel(
            self, 
            text="Unbenutzte Quellspalten als Zusatzfelder registrieren", 
            font=LARGER_LABEL_FONT_BOLD
        )
        header_lbl.pack(padx=PADDING_L, pady=(PADDING_L, PADDING_XS), anchor="w")

        sub_lbl = ctk.CTkLabel(
            self, 
            text="Wähle Spalten aus, die in die Zusatzdaten-Tabellen übernommen werden sollen:", 
            font=LABEL_FONT
        )
        sub_lbl.pack(padx=PADDING_L, pady=(0, PADDING_M), anchor="w")

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Nicht zugeordnete Quellspalten")
        self.scroll_frame.pack(fill="both", expand=True, padx=PADDING_L, pady=PADDING_M)

        headers_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        headers_frame.pack(fill="x", padx=PADDING_XS, pady=2)
        ctk.CTkLabel(headers_frame, text="Übernehmen?", font=SMALL_LABEL_FONT_BOLD, width=HEADER_LABEL_WIDTH).pack(side="left", padx=PADDING_XS)
        ctk.CTkLabel(headers_frame, text="Quellspalte (CSV)", font=SMALL_LABEL_FONT_BOLD, width=REPLACEMENT_INPUT_WIDTH, anchor="w").pack(side="left", padx=PADDING_XS)
        ctk.CTkLabel(headers_frame, text="Zusatzfeld-Name (DB)", font=SMALL_LABEL_FONT_BOLD, width=VALUE_FIELD_WIDTH, anchor="w").pack(side="left", padx=PADDING_XS)
        ctk.CTkLabel(headers_frame, text="Datentyp", font=SMALL_LABEL_FONT_BOLD, width=BUTTON_WIDTH, anchor="w").pack(side="left", padx=PADDING_XS)

        self.row_widgets: List[Dict[str, Any]] = []
        for col_name in self.unmapped_columns:
            self._render_column_row(col_name)

        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=PADDING_L, pady=PADDING_L)

        btn_cancel = ctk.CTkButton(
            footer_frame, text="Überspringen", fg_color=COL_GRAY_40, 
            command=self.destroy
        )
        btn_cancel.pack(side="left")

        btn_apply = ctk.CTkButton(
            footer_frame, text="Zusatzfelder übernehmen & Exportieren", 
            fg_color=COL_DARK_GREEN, hover_color=COL_DARKER_GREEN, font=BUTTON_FONT,
            height=BUTTON_HEIGHT, command=self._on_apply
        )
        btn_apply.pack(side="right")

    def _render_column_row(self, col_name: str) -> None:
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", padx=PADDING_XS, pady=PADDING_XXS)

        var_include = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(row_frame, text="", variable=var_include, width=CHECKBOX_WIDTH)
        chk.pack(side="left", padx=PADDING_M)

        lbl_src = ctk.CTkLabel(row_frame, text=col_name, font=LABEL_FONT_BOLD, width=REPLACEMENT_INPUT_WIDTH, anchor="w")
        lbl_src.pack(side="left", padx=PADDING_XS)

        default_db_name = col_name.lower().strip().replace(" ", "_").replace("-", "_")
        default_db_name = "".join(c for c in default_db_name if c.isalnum() or c == "_")

        entry_name = ctk.CTkEntry(row_frame, width=DB_FIELD_NAMES_WIDTH)
        entry_name.insert(0, default_db_name)
        entry_name.pack(side="left", padx=PADDING_XS)

        combo_proptyp = ctk.CTkOptionMenu(
            row_frame, 
            values=["TXT", "NUM", "DATE", "BOOL"],
            width=DROPDOWN_WIDTH
        )
        combo_proptyp.set("TXT")
        combo_proptyp.pack(side="left", padx=PADDING_XS)

        def toggle_inputs() -> None:
            state = "normal" if var_include.get() else "disabled"
            entry_name.configure(state=state)
            combo_proptyp.configure(state=state)

        chk.configure(command=toggle_inputs)
        toggle_inputs()

        self.row_widgets.append({
            'source_col': col_name,
            'var_include': var_include,
            'entry_name': entry_name,
            'combo_proptyp': combo_proptyp
        })

    def _on_apply(self) -> None:
        self.result_mappings = []
        for rw in self.row_widgets:
            if rw['var_include'].get():
                target_field_name = rw['entry_name'].get().strip()
                if not target_field_name:
                    target_field_name = str(rw['source_col'])
                
                self.result_mappings.append({
                    'source_col': str(rw['source_col']),
                    'field_name': target_field_name,
                    'data_type': str(rw['combo_proptyp'].get())
                })

        self.is_accepted = True
        self.destroy()

class ValidationFixDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, invalid_items: List[Dict[str, Any]]):
        super().__init__(parent)
        self.parent = parent
        self.invalid_items = invalid_items
        self.is_accepted = False

        self.title("⚠️ Validierungsfehler korrigieren")
        center_window(self, VALIDATION_DIALOG_WIDTH, VALIDATION_DIALOG_HEIGHT)
        self.attributes("-topmost", True)  # pyright: ignore[reportUnknownMemberType]
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        header_lbl = ctk.CTkLabel(
            self, 
            text=f"Es wurden {len(self.invalid_items)} ungültige Werte gefunden.", 
            font=LARGER_LABEL_FONT_BOLD,
            text_color=COL_LIGHT_RED
        )
        header_lbl.pack(padx=PADDING_L, pady=(PADDING_L, PADDING_XS), anchor="w")

        sub_lbl = ctk.CTkLabel(
            self, 
            text="Wähle eine globale Aktion oder korrigiere die Einträge einzeln:", 
            font=LABEL_FONT
        )
        sub_lbl.pack(padx=PADDING_L, pady=(0, PADDING_M), anchor="w")

        batch_frame = ctk.CTkFrame(self)
        batch_frame.pack(fill="x", padx=PADDING_L, pady=PADDING_XS)

        ctk.CTkLabel(batch_frame, text="Alle Eintrags-Aktionen:", font=LABEL_FONT_BOLD).pack(side="left", padx=PADDING_M, pady=PADDING_M)
        
        btn_batch_keep = ctk.CTkButton(
            batch_frame, text="Alle beibehalten (Ignorieren)", fg_color=COL_GRAY_40, 
            command=lambda: self._apply_batch_action("keep")
        )
        btn_batch_keep.pack(side="left", padx=PADDING_XS, pady=PADDING_M)

        btn_batch_clear = ctk.CTkButton(
            batch_frame, text="Alle leeren (NULL)", fg_color=COL_LIGHT_RED, 
            command=lambda: self._apply_batch_action("clear")
        )
        btn_batch_clear.pack(side="left", padx=PADDING_XS, pady=PADDING_M)

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Fehlerhafte Einträge")
        self.scroll_frame.pack(fill="both", expand=True, padx=PADDING_L, pady=PADDING_M)

        self.row_widgets: List[Dict[str, Any]] = []
        for idx, item in enumerate(self.invalid_items):
            self._render_item_row(idx, item)

        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=PADDING_L, pady=PADDING_L)

        btn_apply = ctk.CTkButton(
            footer_frame, text="Änderungen übernehmen & Exportieren", 
            fg_color=COL_DARK_GREEN, hover_color=COL_DARKER_GREEN, font=BUTTON_FONT,
            height=BUTTON_HEIGHT, command=self._on_apply
        )
        btn_apply.pack(side="right")

    def _render_item_row(self, idx: int, item: Dict[str, Any]) -> None:
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", padx=PADDING_XS, pady=PADDING_XS)

        rule_desc = "Ungültige IK" if item.get('rule_type') == 'validate_ik' else "Ungültige KVNR"
        info_text = f"Zeile {int(item['row_idx']) + 1} | [{item['target_col']}] ({rule_desc}): '{item['original_val']}'"
        
        lbl = ctk.CTkLabel(row_frame, text=info_text, font=LABEL_FONT_BOLD, anchor="w", width=INFO_LABEL_WIDTH)
        lbl.pack(side="left", padx=PADDING_M, pady=PADDING_XS)

        action_var = ctk.StringVar(value=str(item.get('action', 'keep')))

        entry_custom = ctk.CTkEntry(row_frame, placeholder_text="Manuelle Korrektur", width=MANUAL_CHANGE_FIELD_WIDTH)
        if item.get('custom_val'):
            entry_custom.insert(0, str(item['custom_val']))

        def on_action_change() -> None:
            if action_var.get() == "custom":
                entry_custom.configure(state="normal")
            else:
                entry_custom.configure(state="disabled")

        r_keep = ctk.CTkRadioButton(row_frame, text="Beibehalten", variable=action_var, value="keep", command=on_action_change, width=RADIO_BUTTON_LABEL_WIDTH)
        r_keep.pack(side="left", padx=PADDING_XS)

        r_clear = ctk.CTkRadioButton(row_frame, text="Leeren", variable=action_var, value="clear", command=on_action_change, width=RADIO_BUTTON_LABEL_WIDTH)
        r_clear.pack(side="left", padx=PADDING_XS)

        r_custom = ctk.CTkRadioButton(row_frame, text="Manuell:", variable=action_var, value="custom", command=on_action_change, width=RADIO_BUTTON_LABEL_WIDTH)
        r_custom.pack(side="left", padx=PADDING_XS)

        entry_custom.pack(side="left", padx=PADDING_XS)
        on_action_change()

        self.row_widgets.append({
            'item': item,
            'action_var': action_var,
            'entry_custom': entry_custom
        })

    def _apply_batch_action(self, action: str) -> None:
        for rw in self.row_widgets:
            rw['action_var'].set(action)
            rw['entry_custom'].configure(state="disabled")

    def _on_apply(self) -> None:
        for rw in self.row_widgets:
            action = rw['action_var'].get()
            rw['item']['action'] = action
            rw['item']['custom_val'] = rw['entry_custom'].get().strip()

        self.is_accepted = True
        self.destroy()

class StringCleanupPreviewDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, preview_items: List[Dict[str, Any]]):
        super().__init__(parent)
        self.title("🔍 Vorschau: String-Bereinigung")
        center_window(self, STRING_CLEANUP_DIALOG_WIDTH, STRING_CLEANUP_DIALOG_HEIGHT)
        self.grab_set()
        
        self.preview_items = preview_items
        self.decisions: Dict[int, ctk.BooleanVar] = {i: ctk.BooleanVar(value=True) for i in range(len(preview_items))}
        self.result: List[Dict[str, Any]] | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=PADDING_XL, pady=PADDING_M)
        
        ctk.CTkLabel(
            header_frame, 
            text="String-Bereinigung Vorschau", 
            font=ctk.CTkFont(TITLE_FONT)
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_frame, 
            text=f"Es wurden {len(self.preview_items)} Ersetzungen gefunden. Überprüfe und wähle die gewünschten Änderungen aus:",
            wraplength=REPLACEMENT_WRAP_LENGTH
        ).pack(anchor="w", pady=PADDING_XS)

        global_btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        global_btn_frame.pack(fill="x", padx=PADDING_XL, pady=PADDING_XS)
        
        ctk.CTkButton(
            global_btn_frame, 
            text="✅ Alle auswählen", 
            width=BUTTON_WIDTH, 
            fg_color=COL_GRAY_30,
            command=lambda: self._set_all(True)
        ).pack(side="left", padx=(0, PADDING_M))
        
        ctk.CTkButton(
            global_btn_frame, 
            text="❌ Alle abwählen", 
            width=BUTTON_WIDTH, 
            fg_color=COL_GRAY_30,
            command=lambda: self._set_all(False)
        ).pack(side="left")

        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=PADDING_XL, pady=PADDING_M)

        list_header = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        list_header.pack(fill="x", pady=(0, PADDING_XS))
        ctk.CTkLabel(list_header, text="Anwenden", width=SMALL_HEADER_WIDTH, font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(list_header, text="Zeile / Feld", width=BUTTON_WIDTH, font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=PADDING_XS)
        ctk.CTkLabel(list_header, text="Originalwert", width=LARGE_HEADER_WIDTH, font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=PADDING_XS)
        ctk.CTkLabel(list_header, text="Bereinigter Wert", width=LARGE_HEADER_WIDTH, font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=PADDING_XS)

        for i, item in enumerate(self.preview_items):
            row = ctk.CTkFrame(self.scroll_frame)
            row.pack(fill="x", pady=2, ipady=PADDING_XXS)

            chk = ctk.CTkCheckBox(row, text="", variable=self.decisions[i], width=CHECKBOX_LABEL_WIDTH)
            chk.pack(side="left", padx=PADDING_M)

            info_txt = f"Z. {int(item['row_idx']) + 1} | {item['col_name']}"
            ctk.CTkLabel(row, text=info_txt, width=BUTTON_WIDTH, anchor="w", font=ctk.CTkFont(LABEL_FONT)).pack(side="left", padx=PADDING_XS)

            ctk.CTkLabel(row, text=str(item['original']), width=LARGE_HEADER_WIDTH, anchor="w", text_color=COL_GRAY_70).pack(side="left", padx=PADDING_XS)
            ctk.CTkLabel(row, text="➔", width=PADDING_XL).pack(side="left")
            ctk.CTkLabel(row, text=str(item['cleaned']), width=LARGE_HEADER_WIDTH, anchor="w", text_color=COL_LIGHT_GREEN, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=PADDING_XS)

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=PADDING_XL, pady=PADDING_L)

        ctk.CTkButton(
            bottom_frame, 
            text="Abbrechen", 
            fg_color=COL_GRAY_40, 
            command=self._on_cancel
        ).pack(side="right", padx=(PADDING_M, 0))
        
        ctk.CTkButton(
            bottom_frame, 
            text="Änderungen übernehmen", 
            fg_color=COL_LIGHT_GREEN, 
            hover_color=COL_DARK_GREEN, 
            command=self._on_confirm
        ).pack(side="right")

    def _set_all(self, value: bool) -> None:
        for var in self.decisions.values():
            var.set(value)

    def _on_confirm(self) -> None:
        self.result = [
            self.preview_items[i] 
            for i, var in self.decisions.items() 
            if var.get()
        ]
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()

class ImportApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # 1. Standard-Einstellungen für Auto-Vervollständigung
        self.autocomplete_settings = {
            "split_title": True,            # Titel aus Namen abspalten.
            "infer_gender": True,           # Geschlecht aus Vornamen erkennen.
            "infer_salutation": True,       # Anrede (Herr/Frau) automatisch ergänzen.
            "clean_kvnr": True,             # KVNR auto-korrigieren (O zu 0 etc.).
            "clean_date_formats": True,     # Datumsangaben auf ihr Format prüfen und anpassen.
            "infer_insurance_name": True,   # Krankenkassenname aus IK ableiten.
            "infer_city_name": True,        # Ortsnamen aus PLZ ableiten.
            "infer_plz": True,              # PLZ aus dem Ortsnamen ableiten.
            "validate_email": True,         # E-Mailadresse prüfen.
        }
        # ... dein restlicher Init-Code ...

    def open_autocomplete_settings_dialog(self):
        """Dialogfenster zur An- und Abwahl der Auto-Vervollständigungen"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("⚙️ Einstellungen: Automatische Vervollständigung")
        center_window(dialog, AUTO_COMPLETE_DIALOG_WIDTH, AUTO_COMPLETE_DIALOG_HEIGHT)
        dialog.grab_set()  # Blockiert Eingaben im Hauptfenster

        ctk.CTkLabel(
            dialog, 
            text="Welche Felder sollen automatisch vervollständigt werden?", 
            font=ctk.CTkFont(LARGER_LABEL_FONT_BOLD)
        ).pack(anchor="w", padx=PADDING_XL, pady=(PADDING_XL, PADDING_M))

        # Checkboxen an die aktuellen Einstellungen binden
        vars = {}
        options = [
            ("split_title", "🎓 Titel automatisch von Namen trennen"),
            ("infer_gender", "⚥ Geschlecht anhand des Vornamens erraten"),
            ("infer_salutation", "✉️ Anrede (Herr/Frau) aus Geschlecht/Name abstatten"),
            ("clean_kvnr", "🆔 KVNR automatisch bereinigen (z.B. 'O' -> '0')"),
            ("clean_date_formats", "Datumsformat automatisch korrigieren"),
            ("infer_insurance_name", "Krankenkassenname automatisch ergänzen"),
            ("infer_city_name", "Ortsnamen aus PLZ ableiten"),
            ("infer_plz", "PLZ aus Ortsnamen ableiten"),
            ("validate_email", "E-Mail Adresse validieren")
        ]

        for key, label_text in options:
            var = ctk.BooleanVar(value=self.autocomplete_settings[key])
            chk = ctk.CTkCheckBox(dialog, text=label_text, variable=var)
            chk.pack(anchor="w", padx=PADDING_XXL, pady=PADDING_S)
            vars[key] = var

        def save_and_close():
            for key in vars:
                self.autocomplete_settings[key] = vars[key].get()
            dialog.destroy()

        # Speichern-Button
        btn_save = ctk.CTkButton(
            dialog, 
            text="Übernehmen", 
            command=save_and_close
        )
        btn_save.pack(pady=(PADDING_XL, 0))
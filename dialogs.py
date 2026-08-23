import customtkinter as ctk
from typing import List, Dict, Any, Optional
from constants import (
    ROW_VALIDATION_DIALOG_WIDTH,
    ROW_VALIDATION_DIALOG_HEIGHT,
    EXTRA_FIELDS_DIALOG_WIDTH,
    EXTRA_FIELDS_DIALOG_HEIGHT,
    VALIDATION_DIALOG_WIDTH,
    VALIDATION_DIALOG_HEIGHT,
    STRING_CLEANUP_DIALOG_WIDTH,
    STRING_CLEANUP_DIALOG_HEIGHT,
    AUTO_COMPLETE_DIALOG_WIDTH,
    AUTO_COMPLETE_DIALOG_HEIGHT,
    PADDING_XXS,
    PADDING_XS,
    PADDING_S,
    PADDING_M,
    PADDING_L,
    PADDING_XL,
    PADDING_XXL,
    LARGER_LABEL_FONT_BOLD,
    LABEL_FONT,
    LABEL_FONT_BOLD,
    SMALL_LABEL_FONT,
    SMALL_LABEL_FONT_BOLD,
    BUTTON_FONT,
    TITLE_FONT,
    COLOR_CONTAINER_BG_DARK,
    COLOR_BTN_SECONDARY_BG,
    COLOR_BTN_NEUTRAL_BG,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_BTN_NEUTRAL_HOVER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_DANGER,
    COLOR_BTN_SUCCESS_BG,
    COLOR_BTN_SUCCESS_HOVER,
    COLOR_BTN_SUCCESS_ACTIVE,
    COLOR_ACCENT_SUCCESS,
    COLOR_BTN_TEXT,
    COLOR_BTN_SECONDARY_TEXT,
    BATCH_PROCESS_BUTTON_WIDTH,
    REPLACEMENT_INPUT_WIDTH,
    HEADER_LABEL_WIDTH,
    VALUE_FIELD_WIDTH,
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
    CHECKBOX_WIDTH,
    DB_FIELD_NAMES_WIDTH,
    DROPDOWN_WIDTH,
    MANUAL_CHANGE_FIELD_WIDTH,
    RADIO_BUTTON_LABEL_WIDTH,
    REPLACEMENT_WRAP_LENGTH,
    EXTRA_FIELDS_PROPTYPES,
    AUTOCOMPLETE_OPTIONS_LIST,
    DEFAULT_IMPORT_AUTOCOMPLETE_SETTINGS,
    TITLE_ROW_VALIDATION_DIALOG,
    TITLE_EXTRA_FIELDS_DIALOG,
    TITLE_VALIDATION_FIX_DIALOG,
    TITLE_STRING_CLEANUP_DIALOG,
    TITLE_AUTOCOMPLETE_SETTINGS_DIALOG,
    TXT_BULK_TRUNCATE,
    TXT_BULK_IGNORE,
    TXT_BULK_KEEP,
    TXT_BULK_CLEAR,
    TXT_BULK_CLEAN,
    TXT_BULK_KEEP_CLEANUP,
    TXT_APPLY_EXPORT,
    TXT_APPLY_EXTRA_FIELDS,
    TXT_APPLY_VALIDATION_FIX,
    TXT_APPLY_CONFIRM,
    TXT_CANCEL,
    TXT_SKIP,
    TXT_SAVE,
)


def center_window(window: ctk.CTkToplevel, width: int, height: int) -> None:
    """Zentriert ein CustomTkinter Toplevel-Fenster auf dem Bildschirm."""
    window.update_idletasks()
    screen_width: int = window.winfo_screenwidth()
    screen_height: int = window.winfo_screenheight()
    x: int = (screen_width // 2) - (width // 2)
    y: int = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


class RowValidationDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, conflicts: List[Dict[str, Any]]):
        super().__init__(parent)
        self.title(TITLE_ROW_VALIDATION_DIALOG)
        self.conflicts = conflicts
        self.rows_data: List[Dict[str, Any]] = []
        self.resolved_results: List[Dict[str, Any]] = []
        self.confirmed = False
        center_window(self, ROW_VALIDATION_DIALOG_WIDTH, ROW_VALIDATION_DIALOG_HEIGHT)
        self.grab_set()

        top_frame: ctk.CTkFrame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=PADDING_L, pady=PADDING_M)

        ctk.CTkLabel(top_frame, text=TITLE_ROW_VALIDATION_DIALOG, font=TITLE_FONT).pack(anchor="w", padx=PADDING_M, pady=(PADDING_S, PADDING_XXS))
        ctk.CTkLabel(
            top_frame, 
            text="Gefundene Werte überschreiten das Datenbank-Zeichenlimit des jeweiligen Zielfeldes. Bitte wählen Sie eine Aktion.", 
            font=LABEL_FONT,
            text_color=COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=PADDING_M, pady=(0, PADDING_S))

        global_bar = ctk.CTkFrame(self, fg_color=COLOR_CONTAINER_BG_DARK)
        global_bar.pack(fill="x", padx=PADDING_L, pady=PADDING_XS)

        ctk.CTkLabel(global_bar, text="Massen-Aktion für alle verbleibenden Zeilen:", font=LABEL_FONT_BOLD).pack(side="left", padx=PADDING_M, pady=PADDING_S)

        ctk.CTkButton(
            global_bar, 
            text=TXT_BULK_TRUNCATE, 
            width=BATCH_PROCESS_BUTTON_WIDTH, 
            text_color=COLOR_BTN_SECONDARY_TEXT,
            fg_color=COLOR_BTN_NEUTRAL_BG, 
            hover_color=COLOR_BTN_NEUTRAL_HOVER,
            font=BUTTON_FONT,
            command=self.bulk_truncate
        ).pack(side="left", padx=PADDING_XS, pady=PADDING_S)

        ctk.CTkButton(
            global_bar, 
            text=TXT_BULK_IGNORE, 
            width=BATCH_PROCESS_BUTTON_WIDTH, 
            text_color=COLOR_BTN_SECONDARY_TEXT,
            fg_color=COLOR_BTN_NEUTRAL_BG, 
            hover_color=COLOR_BTN_NEUTRAL_HOVER,
            font=BUTTON_FONT,
            command=self.bulk_keep
        ).pack(side="left", padx=PADDING_XS, pady=PADDING_S)

        self.scroll = ctk.CTkScrollableFrame(self, label_text="Betroffene Tabellenzellen")
        self.scroll.pack(fill="both", expand=True, padx=PADDING_L, pady=PADDING_M)

        for r_idx, item in enumerate(conflicts):
            row_idx: int = int(item['row_idx'])
            col_name: str = str(item['col_name'])
            limit: int = int(item['limit'])
            orig_val: str = str(item['orig_val'])

            card = ctk.CTkFrame(self.scroll)
            card.pack(fill="x", pady=PADDING_XS, padx=PADDING_XS)

            info_txt = f"Zielspalte: {col_name} (Max {limit} Zeichen) | Quellzeile: #{row_idx + 2}"
            lbl_info = ctk.CTkLabel(card, text=info_txt, font=LABEL_FONT_BOLD, text_color=COLOR_TEXT_DANGER)
            lbl_info.pack(anchor="w", padx=PADDING_M, pady=(PADDING_S, PADDING_XXS))

            val_frame = ctk.CTkFrame(card, fg_color="transparent")
            val_frame.pack(fill="x", padx=PADDING_M, pady=PADDING_XS)

            ctk.CTkLabel(val_frame, text="Originaler Wert:", font=SMALL_LABEL_FONT, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(0, PADDING_XS))

            entry_orig = ctk.CTkEntry(val_frame, width=320)
            entry_orig.insert(0, orig_val)
            entry_orig.configure(state="readonly")
            entry_orig.pack(side="left", padx=(0, PADDING_XS))

            btn_copy = ctk.CTkButton(
                val_frame, text="📋", width=30, height=24, text_color=COLOR_BTN_SECONDARY_TEXT, fg_color=COLOR_BTN_NEUTRAL_BG, hover_color=COLOR_BTN_NEUTRAL_HOVER,
                command=lambda v=orig_val: (self.clipboard_clear(), self.clipboard_append(v))
            )
            btn_copy.pack(side="left")

            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.pack(fill="x", padx=PADDING_M, pady=(0, PADDING_S))

            var_action = ctk.StringVar(value="truncate")

            entry_custom = ctk.CTkEntry(action_frame, width=REPLACEMENT_INPUT_WIDTH)
            entry_custom.insert(0, orig_val)

            def on_entry_click(event: Any = None, v_act: ctk.StringVar = var_action) -> None:
                if v_act.get() != "custom":
                    v_act.set("custom")

            entry_custom.bind("<Button-1>", on_entry_click)
            entry_custom.bind("<FocusIn>", on_entry_click)
            entry_custom.bind("<Key>", on_entry_click)

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

        btn_confirm = ctk.CTkButton(
            bottom_bar, 
            text=TXT_APPLY_EXPORT, 
            text_color=COLOR_BTN_TEXT,
            fg_color=COLOR_BTN_SUCCESS_BG, 
            hover_color=COLOR_BTN_SUCCESS_HOVER,
            font=BUTTON_FONT,
            command=self.apply_and_close
        )
        btn_confirm.pack(side="right", padx=PADDING_L)

        btn_cancel = ctk.CTkButton(
            bottom_bar, 
            text=TXT_CANCEL, 
            text_color=COLOR_BTN_SECONDARY_TEXT,
            fg_color=COLOR_BTN_SECONDARY_BG, 
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            font=BUTTON_FONT,
            command=self.cancel
        )
        btn_cancel.pack(side="right", padx=PADDING_XS, pady=PADDING_M)

    def bulk_truncate(self) -> None:
        for r in self.rows_data:
            r['var_action'].set("truncate")

    def bulk_keep(self) -> None:
        for r in self.rows_data:
            r['var_action'].set("ignore")

    def apply_and_close(self) -> None:
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
                'orig_val': orig_val,
                'new_val': final_val,
                'action': action
            })

        self.confirmed = True
        self.destroy()

    def cancel(self) -> None:
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

        self.title(TITLE_EXTRA_FIELDS_DIALOG)
        center_window(self, EXTRA_FIELDS_DIALOG_WIDTH, EXTRA_FIELDS_DIALOG_HEIGHT)
        self.attributes("-topmost", True)  # pyright: ignore[reportUnknownMemberType]
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
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

        btn_skip = ctk.CTkButton(
            footer_frame, text=TXT_SKIP, text_color=COLOR_BTN_SECONDARY_TEXT, fg_color=COLOR_BTN_SECONDARY_HOVER, 
            hover_color=COLOR_BTN_NEUTRAL_HOVER, font=BUTTON_FONT,
            command=self.destroy
        )
        btn_skip.pack(side="right", padx=PADDING_S)

        btn_confirm = ctk.CTkButton(
            footer_frame, text=TXT_APPLY_EXTRA_FIELDS, text_color=COLOR_BTN_TEXT,
            fg_color=COLOR_BTN_SUCCESS_HOVER, hover_color=COLOR_BTN_SUCCESS_ACTIVE, font=BUTTON_FONT,
            command=self._on_apply
        )
        btn_confirm.pack(side="right")

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
            values=EXTRA_FIELDS_PROPTYPES,
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

        self.title(TITLE_VALIDATION_FIX_DIALOG)
        center_window(self, VALIDATION_DIALOG_WIDTH, VALIDATION_DIALOG_HEIGHT)
        self.attributes("-topmost", True)  # pyright: ignore[reportUnknownMemberType]
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        header_lbl = ctk.CTkLabel(
            self, 
            text=f"Es wurden {len(self.invalid_items)} ungültige Werte gefunden.", 
            font=LARGER_LABEL_FONT_BOLD,
            text_color=COLOR_TEXT_DANGER
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
            batch_frame, text=TXT_BULK_KEEP, text_color=COLOR_BTN_SECONDARY_TEXT, fg_color=COLOR_BTN_SECONDARY_BG, hover_color=COLOR_BTN_SECONDARY_HOVER,
            command=lambda: self._apply_batch_action("keep")
        )
        btn_batch_keep.pack(side="left", padx=PADDING_XS, pady=PADDING_M)

        btn_batch_clear = ctk.CTkButton(
            batch_frame, text=TXT_BULK_CLEAR, text_color=COLOR_BTN_TEXT, fg_color=COLOR_TEXT_DANGER, 
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
            footer_frame, text=TXT_APPLY_VALIDATION_FIX, text_color=COLOR_BTN_TEXT,
            fg_color=COLOR_BTN_SUCCESS_HOVER, hover_color=COLOR_BTN_SUCCESS_ACTIVE, font=BUTTON_FONT,
            height=BUTTON_HEIGHT, command=self._on_apply
        )
        btn_apply.pack(side="right")

    def _render_item_row(self, idx: int, item: Dict[str, Any]) -> None:
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", padx=PADDING_XS, pady=PADDING_XS)

        rule_type = str(item.get('rule_type', ''))
        if rule_type == 'validate_ik':
            rule_desc = "Ungültige IK"
        elif rule_type == 'validate_kvnr':
            rule_desc = "Ungültige KVNR"
        elif rule_type == 'validate_email':
            rule_desc = "Ungültige E-Mail"
        else:
            rule_desc = "Ungültiger Wert"

        info_text = f"Zeile {int(item['row_idx']) + 1} | [{item['target_col']}] ({rule_desc}):"
        lbl = ctk.CTkLabel(row_frame, text=info_text, font=LABEL_FONT_BOLD, anchor="w")
        lbl.pack(side="left", padx=(PADDING_M, PADDING_XS), pady=PADDING_XS)

        orig_val = str(item.get('original_val', ''))
        entry_orig = ctk.CTkEntry(row_frame, width=MANUAL_CHANGE_FIELD_WIDTH)
        entry_orig.insert(0, orig_val)
        entry_orig.configure(state="readonly")
        entry_orig.pack(side="left", padx=(0, PADDING_XS))

        btn_copy = ctk.CTkButton(
            row_frame, text="📋", width=30, text_color=COLOR_BTN_SECONDARY_TEXT, fg_color=COLOR_BTN_NEUTRAL_BG, hover_color=COLOR_BTN_NEUTRAL_HOVER,
            command=lambda v=orig_val: (self.clipboard_clear(), self.clipboard_append(v))
        )
        btn_copy.pack(side="left", padx=(0, PADDING_S))

        action_var = ctk.StringVar(value=str(item.get('action', 'keep')))

        entry_custom = ctk.CTkEntry(row_frame, width=MANUAL_CHANGE_FIELD_WIDTH)
        val_to_show = str(item['custom_val']) if item.get('custom_val') else orig_val
        entry_custom.insert(0, val_to_show)

        def on_entry_click(event: Any = None, v_act: ctk.StringVar = action_var) -> None:
            if v_act.get() != "custom":
                v_act.set("custom")

        entry_custom.bind("<Button-1>", on_entry_click)
        entry_custom.bind("<FocusIn>", on_entry_click)
        entry_custom.bind("<Key>", on_entry_click)

        r_keep = ctk.CTkRadioButton(row_frame, text="Beibehalten", variable=action_var, value="keep", width=RADIO_BUTTON_LABEL_WIDTH)
        r_keep.pack(side="left", padx=PADDING_XS)

        r_clear = ctk.CTkRadioButton(row_frame, text="Leeren", variable=action_var, value="clear", width=RADIO_BUTTON_LABEL_WIDTH)
        r_clear.pack(side="left", padx=PADDING_XS)

        r_custom = ctk.CTkRadioButton(row_frame, text="Manuell:", variable=action_var, value="custom", width=RADIO_BUTTON_LABEL_WIDTH)
        r_custom.pack(side="left", padx=PADDING_XS)

        entry_custom.pack(side="left", padx=PADDING_XS)

        self.row_widgets.append({
            'item': item,
            'action_var': action_var,
            'entry_custom': entry_custom
        })

    def _apply_batch_action(self, action: str) -> None:
        for rw in self.row_widgets:
            rw['action_var'].set(action)

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
        self.title(TITLE_STRING_CLEANUP_DIALOG)
        center_window(self, STRING_CLEANUP_DIALOG_WIDTH, STRING_CLEANUP_DIALOG_HEIGHT)
        self.grab_set()
        
        self.preview_items = preview_items
        self.row_widgets: List[Dict[str, Any]] = []
        self.result: List[Dict[str, Any]] | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=PADDING_XL, pady=PADDING_M)
        
        ctk.CTkLabel(
            header_frame, 
            text="String-Bereinigung Vorschau", 
            font=TITLE_FONT
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
            text=TXT_BULK_CLEAN, 
            width=BUTTON_WIDTH, 
            text_color=COLOR_BTN_SECONDARY_TEXT,
            fg_color=COLOR_BTN_SECONDARY_BG,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            command=lambda: self._set_all_action("clean")
        ).pack(side="left", padx=(0, PADDING_M))
        
        ctk.CTkButton(
            global_btn_frame, 
            text=TXT_BULK_KEEP_CLEANUP, 
            width=BUTTON_WIDTH, 
            text_color=COLOR_BTN_SECONDARY_TEXT,
            fg_color=COLOR_BTN_SECONDARY_BG,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            command=lambda: self._set_all_action("keep")
        ).pack(side="left")

        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=PADDING_XL, pady=PADDING_M)

        list_header = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        list_header.pack(fill="x", pady=(0, PADDING_XS))
        ctk.CTkLabel(list_header, text="Zeile / Feld", width=130, font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=PADDING_XS)
        ctk.CTkLabel(list_header, text="Originalwert", width=190, font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=PADDING_XS)
        ctk.CTkLabel(list_header, text="", width=20).pack(side="left")
        ctk.CTkLabel(list_header, text="Vorschlag (Bereinigt)", width=280, font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=PADDING_XS)
        ctk.CTkLabel(list_header, text="Aktionen & Manuell", font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=PADDING_XS)

        for item in self.preview_items:
            self._render_item_row(item)

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=PADDING_XL, pady=PADDING_L)

        ctk.CTkButton(
            bottom_frame, 
            text=TXT_CANCEL, 
            text_color=COLOR_BTN_SECONDARY_TEXT,
            fg_color=COLOR_BTN_SECONDARY_BG, 
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            command=self._on_cancel
        ).pack(side="right", padx=(PADDING_M, 0))
        
        ctk.CTkButton(
            bottom_frame, 
            text=TXT_APPLY_CONFIRM, 
            text_color=COLOR_BTN_TEXT,
            fg_color=COLOR_BTN_SUCCESS_BG, 
            hover_color=COLOR_BTN_SUCCESS_HOVER, 
            command=self._on_confirm
        ).pack(side="right")

    def _render_item_row(self, item: Dict[str, Any]) -> None:
        row = ctk.CTkFrame(self.scroll_frame)
        row.pack(fill="x", pady=2, ipady=PADDING_XXS)

        info_txt = f"Z. {int(item['row_idx']) + 1} | {item['col_name']}"
        ctk.CTkLabel(row, text=info_txt, width=130, anchor="w", font=LABEL_FONT).pack(side="left", padx=PADDING_XS)

        orig_val = str(item['original'])
        cleaned_val = str(item['cleaned'])

        entry_orig = ctk.CTkEntry(row, width=160)
        entry_orig.insert(0, orig_val)
        entry_orig.configure(state="readonly")
        entry_orig.pack(side="left", padx=PADDING_XS)

        btn_copy_orig = ctk.CTkButton(
            row, text="📋", width=30, text_color=COLOR_BTN_SECONDARY_TEXT, fg_color=COLOR_BTN_NEUTRAL_BG, hover_color=COLOR_BTN_NEUTRAL_HOVER,
            command=lambda v=orig_val: (self.clipboard_clear(), self.clipboard_append(v))
        )
        btn_copy_orig.pack(side="left", padx=(0, PADDING_XS))

        ctk.CTkLabel(row, text="➔", width=20).pack(side="left")

        action_var = ctk.StringVar(value="clean")

        r_clean = ctk.CTkRadioButton(row, text="Bereinigen:", variable=action_var, value="clean", width=85)
        r_clean.pack(side="left", padx=PADDING_XS)

        entry_cleaned = ctk.CTkEntry(row, width=160, text_color=COLOR_ACCENT_SUCCESS)
        entry_cleaned.insert(0, cleaned_val)
        entry_cleaned.configure(state="readonly")
        entry_cleaned.pack(side="left", padx=PADDING_XS)

        btn_copy_clean = ctk.CTkButton(
            row, text="📋", width=30, text_color=COLOR_BTN_SECONDARY_TEXT, fg_color=COLOR_BTN_NEUTRAL_BG, hover_color=COLOR_BTN_NEUTRAL_HOVER,
            command=lambda v=cleaned_val: (self.clipboard_clear(), self.clipboard_append(v))
        )
        btn_copy_clean.pack(side="left", padx=(0, PADDING_XS))

        r_keep = ctk.CTkRadioButton(row, text="Beibehalten", variable=action_var, value="keep", width=90)
        r_keep.pack(side="left", padx=PADDING_XS)

        r_custom = ctk.CTkRadioButton(row, text="Manuell:", variable=action_var, value="custom", width=70)
        r_custom.pack(side="left", padx=PADDING_XS)

        entry_custom = ctk.CTkEntry(row, width=160)
        entry_custom.insert(0, cleaned_val)
        entry_custom.pack(side="left", padx=PADDING_XS)

        def on_entry_click(event: Any = None, v_act: ctk.StringVar = action_var) -> None:
            if v_act.get() != "custom":
                v_act.set("custom")

        entry_custom.bind("<Button-1>", on_entry_click)
        entry_custom.bind("<FocusIn>", on_entry_click)
        entry_custom.bind("<Key>", on_entry_click)

        self.row_widgets.append({
            'item': item,
            'action_var': action_var,
            'entry_custom': entry_custom
        })

    def _set_all_action(self, action: str) -> None:
        for rw in self.row_widgets:
            rw['action_var'].set(action)

    def _on_confirm(self) -> None:
        self.result = []
        for rw in self.row_widgets:
            action = rw['action_var'].get()
            orig_val = str(rw['item']['original'])
            cleaned_val = str(rw['item']['cleaned'])
            
            if action == "clean":
                final_val = cleaned_val
            elif action == "custom":
                final_val = rw['entry_custom'].get()
            else:
                final_val = orig_val

            if final_val != orig_val:
                self.result.append({
                    'row_idx': rw['item']['row_idx'],
                    'col_name': rw['item']['col_name'],
                    'original': orig_val,
                    'cleaned': final_val,
                    'action': action
                })
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


class ImportApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.autocomplete_settings = DEFAULT_IMPORT_AUTOCOMPLETE_SETTINGS.copy()

    def open_autocomplete_settings_dialog(self) -> None:
        """Dialogfenster zur An- und Abwahl der Auto-Vervollständigungen"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(TITLE_AUTOCOMPLETE_SETTINGS_DIALOG)
        center_window(dialog, AUTO_COMPLETE_DIALOG_WIDTH, AUTO_COMPLETE_DIALOG_HEIGHT)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, 
            text="Welche Felder sollen automatisch vervollständigt werden?", 
            font=LARGER_LABEL_FONT_BOLD
        ).pack(anchor="w", padx=PADDING_XL, pady=(PADDING_XL, PADDING_M))

        vars_dict: Dict[str, ctk.BooleanVar] = {}
        options = AUTOCOMPLETE_OPTIONS_LIST

        for key, label_text in options:
            var = ctk.BooleanVar(value=self.autocomplete_settings.get(key, True))
            chk = ctk.CTkCheckBox(dialog, text=label_text, variable=var)
            chk.pack(anchor="w", padx=PADDING_XXL, pady=PADDING_S)
            vars_dict[key] = var

        def save_and_close() -> None:
            for key in vars_dict:
                self.autocomplete_settings[key] = vars_dict[key].get()
            dialog.destroy()

        btn_save = ctk.CTkButton(
            dialog, 
            text=TXT_SAVE, 
            command=save_and_close
        )
        btn_save.pack(pady=(PADDING_XL, 0))
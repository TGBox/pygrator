import pytest
from typing import Tuple, Dict
from constants import (
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_DANGER,
    COLOR_TEXT_WARNING,
    COLOR_BTN_TEXT,
    COLOR_BTN_SECONDARY_TEXT,
    COLOR_BTN_SUCCESS_BG,
    COLOR_BTN_SECONDARY_BG,
    COLOR_BTN_NEUTRAL_BG,
    COLOR_CONTAINER_BG_DARK,
    COLOR_CARD_BG,
    COLOR_TOAST_TEXT,
    COLOR_TOAST_BG,
    COLOR_ACCENT_SUCCESS,
)


def hex_to_rgb(hex_str: str) -> Tuple[float, float, float]:
    """Konvertiert einen Hex-Farbcode (#RRGGBB) in float RGB-Werte (0.0 bis 1.0)."""
    clean_hex = hex_str.lstrip("#")
    r = int(clean_hex[0:2], 16) / 255.0
    g = int(clean_hex[2:4], 16) / 255.0
    b = int(clean_hex[4:6], 16) / 255.0
    return r, g, b


def channel_luminance(c: float) -> float:
    """Berechnet die gewichtete Kanalluminanz gemäß sRGB / WCAG 2.1 Standard."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_str: str) -> float:
    """Berechnet die relative Helligkeit (Relative Luminance) einer Hex-Farbe."""
    r, g, b = hex_to_rgb(hex_str)
    return 0.2126 * channel_luminance(r) + 0.7152 * channel_luminance(g) + 0.0722 * channel_luminance(b)


def calculate_contrast_ratio(hex_fg: str, hex_bg: str) -> float:
    """
    Berechnet das WCAG 2.1 Kontrastverhältnis zwischen Vorder- und Hintergrundfarbe.
    Ergebnis ist ein Wert zwischen 1.0 (identisch) und 21.0 (Schwarz-Weiß).
    """
    lum1 = relative_luminance(hex_fg)
    lum2 = relative_luminance(hex_bg)
    l1, l2 = max(lum1, lum2), min(lum1, lum2)
    return (l1 + 0.05) / (l2 + 0.05)


# Liste aller relevanten Farbpaarungen im GUI-Theme: (Vordergrund, Hintergrund, Bezeichnung, Min_Ratio)
THEME_COLOR_PAIRS = [
    (COLOR_TEXT_PRIMARY, COLOR_CONTAINER_BG_DARK, "Haupttext auf Container-Hintergrund", 4.5),
    (COLOR_TEXT_PRIMARY, COLOR_CARD_BG, "Haupttext auf Karten-Hintergrund", 4.5),
    (COLOR_TEXT_MUTED, COLOR_CONTAINER_BG_DARK, "Hinweistext auf Container-Hintergrund", 4.0),
    (COLOR_TEXT_MUTED, COLOR_CARD_BG, "Hinweistext auf Karten-Hintergrund", 4.0),
    (COLOR_TEXT_DANGER, COLOR_CARD_BG, "Fehlertext auf Karten-Hintergrund", 4.0),
    (COLOR_TEXT_WARNING, COLOR_CARD_BG, "Warntext auf Karten-Hintergrund", 4.0),
    (COLOR_BTN_TEXT, COLOR_BTN_SUCCESS_BG, "Buttontext auf Success-Button", 4.0),
    (COLOR_BTN_SECONDARY_TEXT, COLOR_BTN_SECONDARY_BG, "Sekundärtext auf Sekundärbutton", 4.0),
    (COLOR_BTN_SECONDARY_TEXT, COLOR_BTN_NEUTRAL_BG, "Sekundärtext auf Neutralbutton", 4.0),
    (COLOR_TOAST_TEXT, COLOR_TOAST_BG, "Toasttext auf Toast-Hintergrund", 4.5),
    (COLOR_ACCENT_SUCCESS, COLOR_CARD_BG, "Erfolgstext auf Karten-Hintergrund", 4.0),
]


class TestWCAGColorContrast:
    @pytest.mark.parametrize("mode_idx, mode_name", [(0, "Light Mode"), (1, "Dark Mode")])
    def test_all_theme_color_pairs_meet_wcag_contrast(self, mode_idx: int, mode_name: str) -> None:
        """Prüft alle GUI-Farbkombinationen automatisiert auf das WCAG 2.1 Mindest-Kontrastverhältnis."""
        failures = []
        for fg_tuple, bg_tuple, pair_name, min_ratio in THEME_COLOR_PAIRS:
            fg_hex = fg_tuple[mode_idx]
            bg_hex = bg_tuple[mode_idx]
            ratio = calculate_contrast_ratio(fg_hex, bg_hex)
            
            if ratio < min_ratio:
                failures.append(
                    f"[{mode_name}] {pair_name}: {fg_hex} auf {bg_hex} hat Kontrast ratio={ratio:.2f}:1 (Soll min. {min_ratio}:1)"
                )

        assert not failures, "Gefundene Kontrastfehler im GUI-Theme:\n" + "\n".join(failures)

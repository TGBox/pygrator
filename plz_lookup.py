import os
import re
from typing import Optional, List, Dict

class PLZLookupService:
    def __init__(self, filepath: str = "./plz/D.txt") -> None:
        """
        Lädt die PLZ-Datei und baut zwei Indizes für schnellen Zugriff auf:
        - self.plz_to_city: Map von PLZ -> Liste von Ortsnamen (da eine PLZ mehreren Orten gehören kann)
        - self.city_to_plz: Map von Ortsname (kleingeschrieben) -> Liste von PLZs
        """
        self.plz_to_cities: Dict[str, List[str]] = {}
        self.city_to_plzs: Dict[str, List[str]] = {}
        
        if os.path.exists(filepath):
            self._load_file(filepath)
        else:
            print(f"Warnung: PLZ-Datei '{filepath}' wurde nicht gefunden.")

    def _load_file(self, filepath: str) -> None:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Trennung nach 1 oder mehreren Whitespaces / Tabs
                parts = re.split(r'\s+', line)
                
                # Erwartetes Format: [0]=Country, [1]=PLZ, [2]=Ort/Stadtname
                if len(parts) >= 3:
                    plz = parts[1].zfill(5)  # Garantiert 5-stellige PLZ (z. B. '01945')
                    city = parts[2]
                    city_key = city.lower()

                    # 1. PLZ -> Orte Mapping
                    if plz not in self.plz_to_cities:
                        self.plz_to_cities[plz] = []
                    if city not in self.plz_to_cities[plz]:
                        self.plz_to_cities[plz].append(city)

                    # 2. Ort -> PLZs Mapping
                    if city_key not in self.city_to_plzs:
                        self.city_to_plzs[city_key] = []
                    if plz not in self.city_to_plzs[city_key]:
                        self.city_to_plzs[city_key].append(plz)

    def get_city_by_plz(self, plz: str) -> Optional[str]:
        """
        Gibt den ersten passenden Ortsnamen zu einer PLZ zurück.
        Wenn keine Übereinstimmung gefunden wird, wird None zurückgegeben.
        """
        cleaned_plz = str(plz).strip().zfill(5)
        cities = self.plz_to_cities.get(cleaned_plz)
        if cities:
            return cities[0]  # Ersten/Haupt-Ort zurückgeben
        return None

    def get_all_cities_by_plz(self, plz: str) -> List[str]:
        """Gibt ALLE zugeordneten Orte für eine PLZ zurück (z. B. bei Ortsteilen)."""
        cleaned_plz = str(plz).strip().zfill(5)
        return self.plz_to_cities.get(cleaned_plz, [])

    def get_plz_by_city(self, city_name: str) -> Optional[str]:
        """
        Gibt die erste passende PLZ zu einem Ortsnamen zurück (Groß-/Kleinschreibung egal).
        """
        cleaned_city = str(city_name).strip().lower()
        plzs = self.city_to_plzs.get(cleaned_city)
        if plzs:
            return plzs[0]
        return None

    def get_all_plzs_by_city(self, city_name: str) -> List[str]:
        """Gibt ALLE PLZs für einen Ortsnamen zurück (z. B. Großstädte mit vielen PLZs)."""
        cleaned_city = str(city_name).strip().lower()
        return self.city_to_plzs.get(cleaned_city, [])
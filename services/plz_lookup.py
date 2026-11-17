from collections import defaultdict
import os
import re
import sys
from typing import Optional, List, Dict

class PLZLookupService:
    def __init__(self, filepath: Optional[str] = None) -> None:
        """
        Lädt die PLZ-Datei und baut zwei Indizes für schnellen Zugriff auf:
        - self.plz_to_cities: Map von PLZ -> Liste von Ortsnamen
        - self.city_to_plzs: Map von Ortsname (kleingeschrieben) -> Liste von PLZs
        """
        self.plz_to_cities: Dict[str, List[str]] = defaultdict(list)
        self.city_to_plzs: Dict[str, List[str]] = defaultdict(list)
        
        if filepath is None:
            if hasattr(sys, '_MEIPASS'):
                filepath = os.path.join(getattr(sys, '_MEIPASS'), "services", "plz", "D.txt")
            else:
                filepath = "./services/plz/D.txt"

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
                
                parts = re.split(r'\s+', line)
                if len(parts) >= 3:
                    plz = parts[1].zfill(5)
                    city = parts[2]
                    city_key = city.lower()

                    if city not in self.plz_to_cities[plz]:
                        self.plz_to_cities[plz].append(city)
                    if plz not in self.city_to_plzs[city_key]:
                        self.city_to_plzs[city_key].append(plz)

    def get_city_by_plz(self, plz: Optional[str]) -> Optional[str]:
        """Gibt den ersten passenden Ortsnamen zu einer PLZ zurück."""
        if not plz or not plz.strip():
            return None
        cleaned_plz = plz.strip().zfill(5)
        cities = self.plz_to_cities.get(cleaned_plz)
        return cities[0] if cities else None

    def get_plz_by_city(self, city_name: Optional[str]) -> Optional[str]:
        """Gibt die erste passende PLZ zu einem Ortsnamen zurück."""
        if not city_name or not city_name.strip():
            return None
        cleaned_city = city_name.strip().lower()
        plzs = self.city_to_plzs.get(cleaned_city)
        return plzs[0] if plzs else None
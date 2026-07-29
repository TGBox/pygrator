import os
import re
from typing import Optional, List, Dict, Tuple
from difflib import get_close_matches
from rapidfuzz import process, fuzz


class IKLookupService:
    def __init__(self, filepath: str = "./gkv/gkvliste.txt") -> None:
        """
        Lädt die IK-Datei und baut Indizes auf:
        - self.ik_to_provider: Map von IK -> Krankenkassen-Name
        - self.provider_to_ik: Map von Kassen-Name (kleingeschrieben) -> IK
        """
        self.ik_to_provider: Dict[str, str] = {}
        self.provider_to_ik: Dict[str, str] = {}
        self.provider_names_list: List[str] = []

        if os.path.exists(filepath):
            self._load_file(filepath)
        else:
            print(f"Warnung: IK-Datei '{filepath}' wurde nicht gefunden.")

    def _load_file(self, filepath: str) -> None:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Trennung nach 1 oder mehreren Whitespaces/Tabs
                parts = re.split(r'\s+', line)
                
                # Format: [0]=IK, [1..N-3]=Kassen-Name, [-3]=PLZ, [-2]=Ort, [-1]=Straße (oder variierende Rest-Spalten)
                if len(parts) >= 4 and parts[0].isdigit() and len(parts[0]) == 9:
                    ik = parts[0]
                    
                    # Der Name der Krankenkasse kann aus mehreren Wörtern bestehen.
                    # Wir suchen die PLZ (5 Ziffern) von hinten, um das Ende des Namens zu bestimmen.
                    plz_idx = -1
                    for i in range(1, len(parts)):
                        if parts[i].isdigit() and len(parts[i]) == 5:
                            plz_idx = i
                            break
                    
                    if plz_idx != -1:
                        provider_name = " ".join(parts[1:plz_idx])
                    else:
                        # Fallback: Falls keine PLZ erkannt wurde, nimm Teile 1 bis 3
                        provider_name = " ".join(parts[1:3])
                    
                    provider_name = provider_name.strip()
                    if provider_name:
                        self.ik_to_provider[ik] = provider_name
                        self.provider_to_ik[provider_name.lower()] = ik
                        if provider_name not in self.provider_names_list:
                            self.provider_names_list.append(provider_name)

    def get_provider_by_ik(self, ik: str) -> Optional[str]:
        """
        Gibt den Namen der Krankenkasse zu einer gegebenen IK zurück.
        """
        cleaned_ik = str(ik).strip()
        return self.ik_to_provider.get(cleaned_ik, None)

    def get_ik_by_provider(self, name: str, cutoff: float = 0.6, fuzzy: bool = True) -> Tuple[Optional[str], Optional[str], float]:
        """
        Sucht die IK zu einem Krankenkassennamen.
        Führt ein Fuzzy Matching durch, falls kein exakter Treffer gefunden wird.
        
        :param name: Der gesuchte Name der Krankenkasse
        :param cutoff: Schwellenwert für die Ähnlichkeit (0.0 bis 1.0)
        :return: Tuple (gefundene_IK, gefundener_Name, similarity_score)
        """
        cleaned_name = str(name).strip()
        if not cleaned_name:
            return None, None, 0.0

        # 1. Direktes Exaktes Matching (Case-Insensitive)
        exact_match_ik = self.provider_to_ik.get(cleaned_name.lower())
        if exact_match_ik:
            # Den originalen Namen aus dem Dict abrufen
            matched_name = self.ik_to_provider[exact_match_ik]
            return exact_match_ik, matched_name, 1.0

        # 2. Fuzzy Matching
        if fuzzy:
            # Schneller und intelligenter über rapidfuzz (falls vorhanden)
            match = process.extractOne(cleaned_name, self.provider_names_list, scorer=fuzz.WRatio)
            if match and match[1] >= (cutoff * 100):
                best_name = match[0]
                score = match[1] / 100.0
                matched_ik = self.provider_to_ik.get(best_name.lower())
                return matched_ik, best_name, score
        else:
            # Inseitige Standard-Bibliothek (difflib)
            matches = get_close_matches(cleaned_name, self.provider_names_list, n=1, cutoff=cutoff)
            if matches:
                best_name = matches[0]
                matched_ik = self.provider_to_ik.get(best_name.lower())
                return matched_ik, best_name, cutoff  # Approximation

        return None, None, 0.0
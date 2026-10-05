import ast
import re
from pathlib import Path

from constants import RULE_CATEGORIES

PYGRATOR_SRC = Path(__file__).resolve().parent.parent / "pygrator.py"


def _handled_rule_types() -> set[str]:
    """Liest alle rule_type-Zweige aus process_and_export (ohne GUI zu starten)."""
    src = PYGRATOR_SRC.read_text(encoding="utf-8")
    fn = next(
        n for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.FunctionDef) and n.name == "process_and_export"
    )
    body = ast.get_source_segment(src, fn) or ""
    return set(re.findall(r'rule_type\s*==\s*["\'](\w+)["\']', body))


def test_every_selectable_rule_has_export_handler():
    """Jede im Regel-Dialog wählbare Regel muss beim Export auch angewendet werden."""
    missing = set(RULE_CATEGORIES) - _handled_rule_types()
    assert not missing, f"Regeln ohne Export-Logik: {sorted(missing)}"

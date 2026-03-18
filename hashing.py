"""
Funkcije za kreiranje hash-eva (forenzičko logovanje).
"""

import hashlib
import json
from typing import Any


def izracunaj_hash(objekat: Any) -> str:
    """
    Izračunava SHA-256 hash od objekta (pretvorenog u JSON string).
    """
    json_str = json.dumps(objekat, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
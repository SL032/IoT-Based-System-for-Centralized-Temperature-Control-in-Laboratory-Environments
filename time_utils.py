"""
Pomoćne funkcije za rad sa vremenom.
"""

from datetime import datetime


def sada_iso() -> str:
    """Vraća trenutni timestamp u ISO formatu."""
    return datetime.now().isoformat()


def formatiraj_vreme(dt: datetime) -> str:
    """Vraća vreme u formatu YYYY-MM-DD HH:MM:SS."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")
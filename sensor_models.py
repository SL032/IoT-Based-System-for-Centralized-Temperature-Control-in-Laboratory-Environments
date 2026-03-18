"""
Podatkovne klase za senzore i očitavanja.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SensorReading:
    """Jedno očitavanje sa senzora temperature i vlažnosti."""
    zona_id: int
    naziv_zone: str
    temperatura: float          # °C
    vlaznost: float             # %
    timestamp: datetime = field(default_factory=datetime.now)
    validan: bool = True
    poruka_greske: Optional[str] = None
    # Polja za forenzičko logovanje
    prethodni_hash: Optional[str] = None
    hash: Optional[str] = None

    def __str__(self) -> str:
        status = "VALIDAN" if self.validan else f"GRESKA ({self.poruka_greske})"
        return (f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Zona {self.zona_id} – {self.naziv_zone}: "
                f"{self.temperatura:.2f}°C | {self.vlaznost:.1f}% RH  {status}")
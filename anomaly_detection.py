"""
Detekcija anomalija u temperaturnim podacima.
"""

from typing import List, Optional
from collections import deque

from sensors.sensor_models import SensorReading
from database.database_manager import DatabaseManager


class AnomalyDetector:
    """
    Detektuje neuobičajene skokove temperature koristeći pokretnu sredinu i
    standardnu devijaciju. Čuva detektovane anomalije u bazi.
    """

    def __init__(self, db: DatabaseManager, prozor: int = 10, prag: float = 3.0):
        self.db = db
        self.prozor = prozor          # broj prethodnih tačaka za statistiku
        self.prag = prag              # koliko sigma se smatra anomalijom
        self._istorija: dict[int, deque] = {}  # zona_id -> deque temperatura

    def _obezbedi_istoriju(self, zona_id: int) -> deque:
        if zona_id not in self._istorija:
            self._istorija[zona_id] = deque(maxlen=self.prozor)
        return self._istorija[zona_id]

    def proveri(self, o: SensorReading) -> Optional[str]:
        """
        Vraća opis anomalije ako je detektovana, inače None.
        """
        if not o.validan:
            return None

        istorija = self._obezbedi_istoriju(o.zona_id)
        if len(istorija) < self.prozor // 2:
            # Još nemamo dovoljno podataka
            istorija.append(o.temperatura)
            return None

        # Izračunaj sredinu i standardnu devijaciju
        sredina = sum(istorija) / len(istorija)
        var = sum((x - sredina) ** 2 for x in istorija) / len(istorija)
        std = var ** 0.5 if var > 0 else 1.0

        # Dodaj novo očitavanje
        istorija.append(o.temperatura)

        # Provera
        odstupanje = abs(o.temperatura - sredina)
        if odstupanje > self.prag * std:
            opis = (f"Anomalija: temp={o.temperatura:.2f}°C, "
                    f"sredina={sredina:.2f}°C, sigma={std:.2f}, odstupanje={odstupanje:.2f}")
            self.db.sacuvaj_anomaliju(
                o.zona_id, o.naziv_zone, "TEMPERATURNA_ANOMALIJA",
                opis, o.temperatura
            )
            return opis
        return None
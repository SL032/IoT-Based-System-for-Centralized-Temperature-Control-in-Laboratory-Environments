"""
Forenzičko logovanje – dodaje hash lanac prilikom upisa očitavanja.
"""

from typing import Optional
from sensors.sensor_models import SensorReading
from database.database_manager import DatabaseManager
from utils.hashing import izracunaj_hash


class ForensicLogger:
    """
    Omotač oko DatabaseManager koji automatski dodaje hash prethodnog zapisa
    i izračunava sopstveni hash za svako očitavanje.
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._poslednji_hash = db.poslednji_hash()

    def log_ocitavanje(self, o: SensorReading) -> int:
        """
        Upisuje očitavanje u bazu sa hash-em, vraća ID.
        """
        # Izračunaj hash za ovo očitavanje (uključuje prethodni hash)
        podaci_za_hash = {
            "zona_id": o.zona_id,
            "naziv_zone": o.naziv_zone,
            "temperatura": o.temperatura,
            "vlaznost": o.vlaznost,
            "timestamp": o.timestamp.isoformat(),
            "validan": o.validan,
            "prethodni_hash": self._poslednji_hash
        }
        o.hash = izracunaj_hash(podaci_za_hash)
        o.prethodni_hash = self._poslednji_hash

        # Upis u bazu
        id_ = self.db.sacuvaj_ocitavanje(o, self._poslednji_hash)
        self._poslednji_hash = o.hash
        return id_
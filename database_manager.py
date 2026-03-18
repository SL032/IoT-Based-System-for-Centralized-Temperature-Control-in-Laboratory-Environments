"""
Upravljanje SQLite bazom podataka – čuvanje očitavanja, alarma, HVAC naredbi.
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

from sensors.sensor_models import SensorReading
from utils.time_utils import sada_iso


class DatabaseManager:
    """
    Rukuje svim operacijama nad SQLite bazom.
    Obezbeđuje metode za upis i čitanje podataka.
    """

    def __init__(self, putanja: str = "laboratorija.db"):
        self.putanja = putanja
        self._konekcija = sqlite3.connect(putanja, check_same_thread=False)
        self._kreiraj_tabele()

    def _kreiraj_tabele(self):
        cursor = self._konekcija.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS ocitavanja (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                zona_id         INTEGER NOT NULL,
                naziv_zone      TEXT NOT NULL,
                temperatura     REAL NOT NULL,
                vlaznost        REAL NOT NULL,
                timestamp       TEXT NOT NULL,
                validan         INTEGER NOT NULL,
                prethodni_hash  TEXT,
                hash            TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS alarmi (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                zona_id         INTEGER NOT NULL,
                naziv_zone      TEXT NOT NULL,
                tip_alarma      TEXT NOT NULL,
                vrednost        REAL,
                poruka          TEXT,
                timestamp       TEXT NOT NULL,
                aktivan         INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS hvac_naredbe (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                zona_id         INTEGER NOT NULL,
                naredba         TEXT NOT NULL,
                setpoint        REAL,
                timestamp       TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS anomalije (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                zona_id         INTEGER NOT NULL,
                naziv_zone      TEXT NOT NULL,
                tip_anomalije   TEXT NOT NULL,
                opis            TEXT,
                temperatura     REAL,
                timestamp       TEXT NOT NULL
            );
        """)
        self._konekcija.commit()

    def sacuvaj_ocitavanje(self, o: SensorReading, prethodni_hash: Optional[str] = None):
        """Čuva očitavanje sa hash-em prethodnog zapisa i sopstvenim hash-om."""
        hash_tekst = o.hash if o.hash else None
        cursor = self._konekcija.execute(
            """INSERT INTO ocitavanja
               (zona_id, naziv_zone, temperatura, vlaznost, timestamp, validan, prethodni_hash, hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (o.zona_id, o.naziv_zone, o.temperatura, o.vlaznost,
             o.timestamp.isoformat(), int(o.validan), prethodni_hash, hash_tekst)
        )
        self._konekcija.commit()
        return cursor.lastrowid

    def sacuvaj_alarm(self, zona_id: int, naziv: str, tip: str,
                      vrednost: float, poruka: str):
        self._konekcija.execute(
            """INSERT INTO alarmi
               (zona_id, naziv_zone, tip_alarma, vrednost, poruka, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (zona_id, naziv, tip, vrednost, poruka, sada_iso())
        )
        self._konekcija.commit()

    def sacuvaj_hvac_naredbu(self, zona_id: int, naredba: str, setpoint: float):
        self._konekcija.execute(
            """INSERT INTO hvac_naredbe (zona_id, naredba, setpoint, timestamp)
               VALUES (?, ?, ?, ?)""",
            (zona_id, naredba, setpoint, sada_iso())
        )
        self._konekcija.commit()

    def sacuvaj_anomaliju(self, zona_id: int, naziv: str, tip: str,
                          opis: str, temperatura: float):
        self._konekcija.execute(
            """INSERT INTO anomalije (zona_id, naziv_zone, tip_anomalije, opis, temperatura, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (zona_id, naziv, tip, opis, temperatura, sada_iso())
        )
        self._konekcija.commit()

    def poslednja_ocitavanja(self, zona_id: int, n: int = 10) -> List[Dict[str, Any]]:
        cursor = self._konekcija.execute(
            """SELECT temperatura, vlaznost, timestamp FROM ocitavanja
               WHERE zona_id = ? ORDER BY id DESC LIMIT ?""",
            (zona_id, n)
        )
        return [{"temperatura": r[0], "vlaznost": r[1], "timestamp": r[2]}
                for r in cursor.fetchall()]

    def aktivni_alarmi(self) -> List[Dict[str, Any]]:
        cursor = self._konekcija.execute(
            """SELECT zona_id, naziv_zone, tip_alarma, vrednost, poruka, timestamp
               FROM alarmi WHERE aktivan = 1 ORDER BY id DESC"""
        )
        keys = ["zona_id", "naziv_zone", "tip_alarma", "vrednost", "poruka", "timestamp"]
        return [dict(zip(keys, row)) for row in cursor.fetchall()]

    def deaktiviraj_alarm(self, alarm_id: int):
        self._konekcija.execute(
            "UPDATE alarmi SET aktivan = 0 WHERE id = ?", (alarm_id,)
        )
        self._konekcija.commit()

    def statistika_zone(self, zona_id: int) -> Dict[str, Any]:
        cursor = self._konekcija.execute(
            """SELECT
                   COUNT(*)          AS broj,
                   AVG(temperatura)  AS avg_temp,
                   MIN(temperatura)  AS min_temp,
                   MAX(temperatura)  AS max_temp,
                   AVG(vlaznost)     AS avg_vlaz
               FROM ocitavanja WHERE zona_id = ? AND validan = 1""",
            (zona_id,)
        )
        row = cursor.fetchone()
        if not row or row[0] == 0:
            return {}
        return {
            "broj_merenja": row[0],
            "avg_temp":     round(row[1], 2),
            "min_temp":     round(row[2], 2),
            "max_temp":     round(row[3], 2),
            "avg_vlaz":     round(row[4], 1),
        }

    def poslednji_hash(self) -> Optional[str]:
        """Vraća hash poslednjeg upisanog očitavanja (za lančanje)."""
        cursor = self._konekcija.execute(
            "SELECT hash FROM ocitavanja WHERE hash IS NOT NULL ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def zatvori(self):
        self._konekcija.close()
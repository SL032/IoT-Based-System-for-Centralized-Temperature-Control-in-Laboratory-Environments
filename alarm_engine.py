"""
Provera graničnih vrednosti i generisanje alarma.
"""

from typing import List, Tuple, Optional
from datetime import datetime, timedelta

from config.zone_config import ZoneConfig
from sensors.sensor_models import SensorReading
from database.database_manager import DatabaseManager


# Tipovi alarma
ALARM_VISOKA_TEMP   = "VISOKA_TEMPERATURA"
ALARM_NISKA_TEMP    = "NISKA_TEMPERATURA"
ALARM_VISOKA_VLAZ   = "VISOKA_VLAZNOST"
ALARM_SENZOR_GRESKA = "GRESKA_SENZORA"


class AlarmEngine:
    """
    Proverava da li očitavanje prelazi definisane granice.
    Vodi računa o duplikatima: ne generiše isti alarm više puta u kratkom roku.
    """

    def __init__(self, db: DatabaseManager, debounce_sekundi: int = 60):
        self.db = db
        self.debounce_sekundi = debounce_sekundi
        self._poslednji_alarmi: dict[Tuple[int, str], datetime] = {}

    def proveri(self, o: SensorReading, config: ZoneConfig) -> List[str]:
        """
        Vraća listu opisa alarma koji su se desili (prazno ako nema novih).
        """
        alarmi = []
        sada = datetime.now()

        if not o.validan:
            self._generisi_alarm_ako_nije_skoro(
                o.zona_id, o.naziv_zone, ALARM_SENZOR_GRESKA, 0.0,
                o.poruka_greske or "Nevalidan senzor", sada, alarmi
            )
            return alarmi

        # Temperatura visoka
        if o.temperatura > config.granica_max:
            poruka = f"Temperatura {o.temperatura:.1f}°C > max {config.granica_max}°C"
            self._generisi_alarm_ako_nije_skoro(
                o.zona_id, o.naziv_zone, ALARM_VISOKA_TEMP, o.temperatura,
                poruka, sada, alarmi
            )

        # Temperatura niska
        elif o.temperatura < config.granica_min:
            poruka = f"Temperatura {o.temperatura:.1f}°C < min {config.granica_min}°C"
            self._generisi_alarm_ako_nije_skoro(
                o.zona_id, o.naziv_zone, ALARM_NISKA_TEMP, o.temperatura,
                poruka, sada, alarmi
            )

        # Vlažnost visoka
        if o.vlaznost > config.granica_vlaz_max:
            poruka = f"Vlažnost {o.vlaznost:.1f}% > max {config.granica_vlaz_max}%"
            self._generisi_alarm_ako_nije_skoro(
                o.zona_id, o.naziv_zone, ALARM_VISOKA_VLAZ, o.vlaznost,
                poruka, sada, alarmi
            )

        return alarmi

    def _generisi_alarm_ako_nije_skoro(self, zona_id: int, naziv: str, tip: str,
                                        vrednost: float, poruka: str,
                                        sada: datetime, alarmi_lista: List[str]):
        kljuc = (zona_id, tip)
        poslednji = self._poslednji_alarmi.get(kljuc)
        if poslednji and (sada - poslednji) < timedelta(seconds=self.debounce_sekundi):
            return  # preskoči duplikat
        self._poslednji_alarmi[kljuc] = sada
        self.db.sacuvaj_alarm(zona_id, naziv, tip, vrednost, poruka)
        alarmi_lista.append(poruka)
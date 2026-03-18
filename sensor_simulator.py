"""
Simulacija fizičkog ponašanja senzora u laboratorijskoj zoni.
"""

import random
import math
from datetime import datetime
from typing import Optional

from config.zone_config import ZoneConfig
from sensors.sensor_models import SensorReading


# Fizička ograničenja senzora
TEMP_MIN = 15.0   # °C
TEMP_MAX = 40.0
VLAZ_MIN = 20.0   # %
VLAZ_MAX = 95.0
SUMA_BUKE = 0.3   # °C standardna devijacija


class SensorSimulator:
    """
    Simulira realno termičko ponašanje jedne laboratorijske zone:
    - sporo oscilovanje temperature oko setpointa
    - slučajni poremećaji (otvaranje vrata, rad opreme)
    - šum senzora
    - povremeni kvarovi (nevalidna očitavanja)
    """

    def __init__(self, config: ZoneConfig, kvar_verovatnoca: float = 0.005):
        self.config = config
        self.kvar_verovatnoca = kvar_verovatnoca
        self._temp_stvarna = config.setpoint_temp + random.uniform(-1.5, 1.5)
        self._vlaz_stvarna = 45.0 + random.uniform(-5, 5)
        self._faza = random.uniform(0, 2 * math.pi)
        self._korak = 0

    def _azuriraj_stanje(self):
        """Korak simulacije – ažurira interno stanje zone."""
        self._korak += 1

        # Prirodna oscilacija (sinus, period ~120 koraka)
        oscilacija = 0.8 * math.sin(2 * math.pi * self._korak / 120 + self._faza)

        # Slučajni poremećaj (otvaranje vrata, rad opreme)
        poremecaj = 0.0
        if random.random() < 0.01:
            poremecaj = random.uniform(-2.0, 3.5)

        # Drift ka setpointu
        razlika = self.config.setpoint_temp - self._temp_stvarna
        drift = 0.05 * razlika

        self._temp_stvarna += drift + oscilacija * 0.02 + poremecaj
        self._temp_stvarna = max(TEMP_MIN, min(TEMP_MAX, self._temp_stvarna))

        # Vlažnost – slabo korelisana sa temperaturom
        self._vlaz_stvarna += random.gauss(0, 0.3)
        self._vlaz_stvarna = max(VLAZ_MIN, min(VLAZ_MAX, self._vlaz_stvarna))

    def ocitaj(self) -> SensorReading:
        """Vraća novo očitavanje, sa mogućnošću kvara."""
        self._azuriraj_stanje()

        # Da li senzor otkazuje?
        if random.random() < self.kvar_verovatnoca:
            return SensorReading(
                zona_id=self.config.zona_id,
                naziv_zone=self.config.naziv,
                temperatura=random.uniform(-50, 100),  # potpuno van opsega
                vlaznost=random.uniform(0, 120),
                validan=False,
                poruka_greske="Senzor u kvaru (simulacija)"
            )

        # Dodaj šum merenja
        temp_izmerena = round(self._temp_stvarna + random.gauss(0, SUMA_BUKE), 2)
        vlaz_izmerena = round(self._vlaz_stvarna + random.gauss(0, 0.5), 1)

        # Validacija opsega
        validan = True
        poruka = None
        if not (TEMP_MIN <= temp_izmerena <= TEMP_MAX):
            validan = False
            poruka = f"Temperatura {temp_izmerena}°C van opsega"
        if not (VLAZ_MIN <= vlaz_izmerena <= VLAZ_MAX):
            validan = False
            poruka = (poruka or "") + f" Vlažnost {vlaz_izmerena}% van opsega"

        return SensorReading(
            zona_id=self.config.zona_id,
            naziv_zone=self.config.naziv,
            temperatura=temp_izmerena,
            vlaznost=vlaz_izmerena,
            validan=validan,
            poruka_greske=poruka
        )
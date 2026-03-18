"""
Simulacija ESP32 mikrokontrolera koji prikuplja podatke sa senzora.
"""
import random
import time
from typing import List, Callable, Optional

from config.zone_config import ZoneConfig
from sensors.sensor_simulator import SensorSimulator
from sensors.sensor_models import SensorReading


class ESP32Controller:
    """
    Simulira ESP32 – prikuplja očitavanja iz svih zona i prosleđuje ih serveru.
    Može simulirati kašnjenje u komunikaciji ili gubitak paketa.
    """

    def __init__(self, zone_configs: List[ZoneConfig], interval_s: float = 5.0,
                 gubitak_paketa: float = 0.0, latencija_s: float = 0.1):
        self.interval_s = interval_s
        self.gubitak_paketa = gubitak_paketa      # verovatnoća gubitka paketa
        self.latencija_s = latencija_s
        self._simulatori = {cfg.zona_id: SensorSimulator(cfg) for cfg in zone_configs}
        self._ukupno_ocitavanja = 0
        self._greske = 0

    def prikupi_sve_zone(self) -> List[SensorReading]:
        """Prikuplja jedno očitavanje sa svakog senzora."""
        ocitavanja = []
        for zona_id, sim in self._simulatori.items():
            ocit = sim.ocitaj()
            self._ukupno_ocitavanja += 1
            if not ocit.validan:
                self._greske += 1
            ocitavanja.append(ocit)
        return ocitavanja

    def status(self) -> dict:
        """Dijagnostički podaci ESP32."""
        return {
            "ukupno_ocitavanja": self._ukupno_ocitavanja,
            "greske": self._greske,
            "pouzdanost_proc": round(
                (1 - self._greske / max(1, self._ukupno_ocitavanja)) * 100, 1
            ),
            "broj_zona": len(self._simulatori)
        }

    def pokreni_kontinualno(self, trajanje_s: float, callback: Callable[[List[SensorReading]], None]):
        """
        Kontinualno prikuplja podatke u zadatom trajanju i poziva callback.
        Simulira latenciju i gubitak paketa.
        """
        pocetak = time.time()
        ciklus = 0
        print("\n" + "="*60)
        print("  ESP32 – pokretanje prikupljanja podataka")
        print(f"  Interval: {self.interval_s}s | Trajanje: {trajanje_s}s")
        print("="*60 + "\n")

        while time.time() - pocetak < trajanje_s:
            ciklus += 1
            print(f"--- Ciklus {ciklus} ---")

            # Simulacija gubitka paketa
            if random.random() < self.gubitak_paketa:
                print("  [ESP32] Paket izgubljen (simulacija)")
                time.sleep(self.interval_s)
                continue

            # Simulacija latencije
            time.sleep(self.latencija_s)

            ocitavanja = self.prikupi_sve_zone()
            for o in ocitavanja:
                print(f"  {o}")

            callback(ocitavanja)

            time.sleep(self.interval_s)

        print(f"\nESP32 završio. Status: {self.status()}\n")
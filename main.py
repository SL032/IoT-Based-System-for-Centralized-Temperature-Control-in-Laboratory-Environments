"""
Glavni ulazni fajl – pokreće simulaciju celokupnog sistema.
"""

import sys
import os

# Dodaj trenutni direktorijum u putanju
sys.path.insert(0, os.path.dirname(__file__))

from config.zone_config import DEFAULT_ZONES
from sensors.esp32_controller import ESP32Controller
from server.server_core import Server


def main():
    print("\n" + "="*70)
    print("  IoT SISTEM ZA CENTRALIZOVANU KONTROLU TEMPERATURE")
    print("  Laboratorijski prostor – Simulacija sa forenzičkim logovanjem")
    print("="*70)

    # Inicijalizacija servera
    server = Server(zone_configs=DEFAULT_ZONES, db_path="laboratorija.db")

    # Inicijalizacija ESP32 kontrolera (simulacija)
    esp32 = ESP32Controller(
        zone_configs=DEFAULT_ZONES,
        interval_s=2.0,
        gubitak_paketa=0.02,      # 2% šanse da se paket izgubi
        latencija_s=0.1
    )

    # Callback za slanje podataka serveru
    def posalji_serveru(ocitavanja):
        server.obradi_ocitavanja(ocitavanja)
        # Prikaži dashboard svakih 10 ciklusa
        if hasattr(posalji_serveru, "brojac") is False:
            posalji_serveru.brojac = 0
        posalji_serveru.brojac += 1
        if posalji_serveru.brojac % 5 == 0:
            server.dashboard.prikazi()

    try:
        # Pokreni prikupljanje na 60 sekundi
        esp32.pokreni_kontinualno(trajanje_s=60.0, callback=posalji_serveru)

        # Završni prikaz
        print("\n--- ZAVRSNI IZVESTAJ ---")
        server.dashboard.prikazi()

    except KeyboardInterrupt:
        print("\n\nPrekid od strane korisnika.")
    finally:
        server.zatvori()
        print("Sistem zaustavljen.\n")


if __name__ == "__main__":
    main()
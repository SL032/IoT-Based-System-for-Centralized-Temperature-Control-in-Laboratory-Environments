"""
Definicija konfiguracije laboratorijskih zona.
"""

from dataclasses import dataclass


@dataclass
class ZoneConfig:
    """Konfiguracija jedne zone."""
    zona_id: int
    naziv: str
    setpoint_temp: float        # °C – željena temperatura
    granica_min: float           # °C – donja alarmna granica
    granica_max: float           # °C – gornja alarmna granica
    granica_vlaz_max: float      # %  – maksimalna dozvoljena vlažnost


# Podrazumevana konfiguracija (može se učitati iz JSON fajla)
DEFAULT_ZONES = [
    ZoneConfig(1, "Hemijska laboratorija", 20.0, 17.0, 23.0, 60.0),
    ZoneConfig(2, "Mikrobiološka laboratorija", 22.0, 20.0, 25.0, 55.0),
    ZoneConfig(3, "Serverska soba", 18.0, 16.0, 21.0, 50.0),
]
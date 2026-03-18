"""
Centralni server – koordinira sve komponente.
"""

from typing import List, Dict

from config.zone_config import ZoneConfig
from sensors.sensor_models import SensorReading
from database.database_manager import DatabaseManager
from database.forensic_logger import ForensicLogger
from server.alarm_engine import AlarmEngine
from server.hvac_controller import HVACController
from server.anomaly_detection import AnomalyDetector
from dashboard.dashboard_service import DashboardService


class Server:
    """
    Implementira serversku komponentu (7) iz patentne prijave.
    """

    def __init__(self, zone_configs: List[ZoneConfig], db_path: str = "laboratorija.db"):
        self.zone_configs = {cfg.zona_id: cfg for cfg in zone_configs}
        self.db = DatabaseManager(db_path)
        self.forensic = ForensicLogger(self.db)
        self.alarm_engine = AlarmEngine(self.db)
        self.hvac = HVACController(self.db)
        self.anomaly = AnomalyDetector(self.db)
        self.dashboard = DashboardService(self)
        self._broj_obrada = 0

    def obradi_ocitavanja(self, ocitavanja: List[SensorReading]):
        """
        Obrada paketa podataka sa ESP32.
        """
        self._broj_obrada += 1
        print(f"\n  [SERVER] Obrada paketa #{self._broj_obrada}")

        for o in ocitavanja:
            # 1. Forenzičko logovanje
            self.forensic.log_ocitavanje(o)

            # 2. Provera alarma
            config = self.zone_configs.get(o.zona_id)
            if config:
                alarmi = self.alarm_engine.proveri(o, config)
                for a in alarmi:
                    print(f"    [ALARM] Zona {o.zona_id}: {a}")

                # 3. HVAC regulacija
                hvac_naredba = self.hvac.regulisi(o.zona_id, config.setpoint_temp, o.temperatura)
                print(f"    [HVAC] Zona {o.zona_id}: {hvac_naredba}")

                # 4. Detekcija anomalija
                anomalija = self.anomaly.proveri(o)
                if anomalija:
                    print(f"    [ANOMALIJA] Zona {o.zona_id}: {anomalija}")
            else:
                print(f"    [UPOZORENJE] Nepoznata zona_id {o.zona_id}")

    def dashboard_podaci(self) -> Dict:
        """Prikuplja podatke za prikaz na dashboard-u."""
        podaci = {
            "timestamp": self.db.poslednja_ocitavanja(1, 1)[0]["timestamp"]
                        if self.db.poslednja_ocitavanja(1, 1) else "",
            "zone": {},
            "aktivni_alarmi": self.db.aktivni_alarmi(),
        }
        for zona_id, config in self.zone_configs.items():
            posled = self.db.poslednja_ocitavanja(zona_id, 1)
            stat = self.db.statistika_zone(zona_id)
            podaci["zone"][zona_id] = {
                "naziv": config.naziv,
                "setpoint": config.setpoint_temp,
                "poslednje": posled[0] if posled else None,
                "statistika": stat,
                "hvac_status": self.hvac._poslednja_naredba.get(zona_id, "NEPOZNATO"),
            }
        return podaci

    def zatvori(self):
        self.db.zatvori()
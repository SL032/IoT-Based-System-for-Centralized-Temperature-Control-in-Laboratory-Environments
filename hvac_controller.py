"""
PID regulator za upravljanje HVAC sistemom.
"""

from typing import Dict


class PIDController:
    """
    Proporcionalno-integralno-derivativni regulator.
    Izlaz: snaga HVAC sistema u % (-100 hladi, +100 greje).
    """

    def __init__(self, kp: float = 2.0, ki: float = 0.05, kd: float = 0.5):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self._integral = 0.0
        self._prethodna_greska = 0.0

    def izracunaj(self, setpoint: float, izmereno: float, dt: float = 5.0) -> float:
        greska = setpoint - izmereno
        self._integral += greska * dt
        # Anti-windup
        self._integral = max(-100.0, min(100.0, self._integral))
        derivat = (greska - self._prethodna_greska) / dt
        self._prethodna_greska = greska
        izlaz = self.kp * greska + self.ki * self._integral + self.kd * derivat
        return max(-100.0, min(100.0, round(izlaz, 1)))

    def resetuj(self):
        self._integral = 0.0
        self._prethodna_greska = 0.0


class HVACController:
    """
    Upravlja HVAC sistemom na osnovu PID regulatora i čuva naredbe u bazi.
    """

    def __init__(self, db):
        self.db = db
        self._pid: Dict[int, PIDController] = {}
        self._poslednja_naredba: Dict[int, str] = {}

    def _obezbedi_pid(self, zona_id: int) -> PIDController:
        if zona_id not in self._pid:
            self._pid[zona_id] = PIDController()
        return self._pid[zona_id]

    def regulisi(self, zona_id: int, setpoint: float, temperatura: float) -> str:
        pid = self._obezbedi_pid(zona_id)
        izlaz = pid.izracunaj(setpoint, temperatura)

        if izlaz > 10:
            naredba = f"GREJANJE {izlaz:.0f}%"
        elif izlaz < -10:
            naredba = f"HLADJENJE {abs(izlaz):.0f}%"
        else:
            naredba = "STANDBY (temperatura u opsegu)"

        # Sačuvaj samo ako se promenila
        if self._poslednja_naredba.get(zona_id) != naredba:
            self.db.sacuvaj_hvac_naredbu(zona_id, naredba, setpoint)
            self._poslednja_naredba[zona_id] = naredba

        return naredba
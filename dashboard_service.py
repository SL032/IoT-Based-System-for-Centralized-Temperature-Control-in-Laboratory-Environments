"""
Servis za generisanje preglednog izveštaja (dashboard).
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server.server_core import Server


class DashboardService:
    """
    Priprema i ispisuje dashboard na konzolu.
    """

    def __init__(self, server: 'Server'):
        self.server = server

    def prikazi(self):
        """Ispisuje trenutno stanje sistema."""
        podaci = self.server.dashboard_podaci()
        print("\n" + "="*70)
        print(f"  DASHBOARD  {podaci['timestamp']}")
        print("="*70)

        for zid, z in podaci["zone"].items():
            p = z["poslednje"]
            s = z["statistika"]
            print(f"\n  Zona {zid}: {z['naziv']}")
            print(f"    Setpoint   : {z['setpoint']}°C")
            if p:
                print(f"    Trenutno   : {p['temperatura']}°C | {p['vlaznost']}% RH")
            if s:
                print(f"    Statistika : avg={s.get('avg_temp')}°C  "
                      f"min={s.get('min_temp')}°C  max={s.get('max_temp')}°C")
            print(f"    HVAC       : {z['hvac_status']}")

        alarmi = podaci["aktivni_alarmi"]
        if alarmi:
            print(f"\n  AKTIVNI ALARMI ({len(alarmi)}):")
            for a in alarmi[:5]:
                print(f"     [{a['timestamp'][:19]}] {a['tip_alarma']} – {a['poruka']}")
        else:
            print("\n  Nema aktivnih alarma")

        print("="*70 + "\n")
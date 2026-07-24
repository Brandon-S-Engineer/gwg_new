"""Ectos: salvage de globs of ectoplasm y venta del crystalline dust.

Salvage rinde más oro que vender los ectos directo. Cada ecto suelta pile of
crystalline dust, que después vendemos en el TP.

Corre cada 30 iteraciones en el segmento GREEN (schedule.TASKS_GREEN):
  1. Salvage de TODOS los stacks de ectos (con silver_fed, infinito).
  2. Vender TODOS los stacks de dust. Al primero -1 copper para vender
     primero; del segundo en adelante NO, para no taparme a mí mismo.

Coords del kit (silver_fed*) y minus_one_copper ya calibradas en el json.
"""

import time

from . import sell
from .. import input as inp
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point, get_region

ECTO = ITEMS_DIR / "globs_of_ectoplasm.png"
DUST = "pile_of_cristallyne_dust"   # nombre del item (sell.sell_item arma el .png)

ECTO_THRESHOLD = 0.85
DUST_THRESHOLD = 0.85

MAX_STACKS = 12   # tope de seguridad, no loop infinito

# Tiempos centralizados en schedule.py para calibrarlos en un solo lugar.
SLEEP_AFTER_RIGHT_CLICK = schedule.ECTOS_AFTER_RIGHT_CLICK
SLEEP_AFTER_OPTION = schedule.ECTOS_AFTER_OPTION
SLEEP_AFTER_SALVAGE = schedule.ECTOS_AFTER_SALVAGE


def _salvage_one(spot: tuple[int, int]) -> None:
    inp.right_click(get_point("silver_fed"))
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    inp.click(get_point("silver_fed_salvage_stack"))
    time.sleep(SLEEP_AFTER_OPTION)
    inp.click(spot)                                   # elegir el stack de ectos
    time.sleep(SLEEP_AFTER_OPTION)
    inp.click(get_point("silver_fed_salvage_stack_accept"))
    time.sleep(SLEEP_AFTER_SALVAGE)


def salvage_all_ectos() -> bool:
    """Salvagea cada stack de ectos del inventario. Re-escanea tras cada uno."""
    done = False
    for _ in range(MAX_STACKS):
        spot = vision.find(ECTO, region=get_region("INVENTORY_AREA"),
                           threshold=ECTO_THRESHOLD)
        if not spot:
            break
        print(f"[ectos] ecto en {spot}, salvage...")
        _salvage_one(spot)
        done = True
    if not done:
        print("[ectos] no hay ectos para salvage")
    return done


def sell_all_dust(undercut: bool = True) -> bool:
    """Vende cada stack de dust. -1 copper solo al primero (undercut=True,
    default — así corre en green, cada 30 iteraciones: bajar 1 copper de
    vez en cuando está bien). En yellow (TASKS_YELLOW pasa undercut=False)
    corre cada iteración por los ~222 ectos/stack; bajar 1 copper tan
    seguido empujaría el precio hacia abajo y me taparía a mí mismo."""
    done = False
    first = True
    for _ in range(MAX_STACKS):
        if not sell.sell_item(DUST, threshold=DUST_THRESHOLD, undercut=undercut and first):
            break
        done = True
        first = False
    if not done:
        print("[ectos] no hay crystalline dust para vender")
    return done


def run(undercut: bool = True) -> bool:
    print("[ectos] salvage de ectos + venta de dust...")
    salvage_all_ectos()
    sold = sell_all_dust(undercut=undercut)
    print("[ectos] OK")
    return sold

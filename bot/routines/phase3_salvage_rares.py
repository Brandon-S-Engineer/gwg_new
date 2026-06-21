"""Fase 3: salvage de rares con Silver-Fed Salvage-o-Matic.

Mismo flujo que el rune_crafter de fase 1:
  1. right-click sobre el kit silver_fed.
  2. click en la opción "salvage rares".
  3. click en "Accept" por template (salvage.click_accept) — es el mismo botón.

OJO: las coords silver_fed del json están en x negativa (rotas). Recalibrar
con el picker antes de usar esto.
"""

import time

from .. import dialogs
from .. import input as inp
from .. import salvage
from .. import schedule
from ..coords_loader import get_point

# Tiempos centralizados en schedule.py para calibrarlos en un solo lugar.
SLEEP_AFTER_RIGHT_CLICK = schedule.PHASE3_AFTER_RIGHT_CLICK
SLEEP_AFTER_OPTION = schedule.PHASE3_AFTER_OPTION
SLEEP_AFTER_SALVAGE = schedule.PHASE3_AFTER_SALVAGE


def salvage_with_silver_fed() -> bool:
    inp.right_click(get_point("silver_fed"))
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    inp.click(get_point("silver_fed_salvage_rare"))
    time.sleep(SLEEP_AFTER_OPTION)
    return salvage.click_accept()


def run() -> bool:
    print("[fase3] salvage de rares con silver_fed...")
    ok = salvage_with_silver_fed()
    dialogs.sleep_safe(SLEEP_AFTER_SALVAGE)
    print("[fase3] OK" if ok else "[fase3] no apareció Accept (¿coords silver_fed?)")
    return ok

"""Guardar Esencia de Suerte al banco con doble-click.

Busca en SELL_SEARCH_AREA (no en inventario) y compacta antes de buscar
para que los stacks estén juntos. Purple se ignora (sale muy poco).

Usar desde schedule con lambdas por tier:
    (1,  lambda: store_luck.run(store_luck.BLUE))
    (6,  lambda: store_luck.run(store_luck.GREEN))
    (30, lambda: store_luck.run(store_luck.YELLOW))
"""

import time

from .. import input as inp
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point, get_region

BLUE   = ITEMS_DIR / "blue_luck.png"
GREEN  = ITEMS_DIR / "green_luck.png"
YELLOW = ITEMS_DIR / "yellow_luck.png"

LUCK_THRESHOLD = 0.80

SLEEP_AFTER_COMPACT    = 0.5
SLEEP_AFTER_DOUBLECLICK = 0.5


def run(template) -> bool:
    inp.click(get_point("compact"))
    time.sleep(SLEEP_AFTER_COMPACT)

    spot = vision.find(template, region=get_region("SELL_SEARCH_AREA"),
                       threshold=LUCK_THRESHOLD, color=True)
    if not spot:
        print(f"[store_luck] {template.name}: no encontrada")
        return False

    print(f"[store_luck] {template.name} en {spot}, doble-click → banco")
    inp.double_click(spot)
    time.sleep(SLEEP_AFTER_DOUBLECLICK)
    return True

"""Fase 2: consumir Esencia de Suerte (puro estorbo de inventario).

Las 4 tiers (blue/green/yellow/purple) se limpian con right-click → "Consume All".
Mismo patrón que el "Use All" de fase 1, pero el menú de la esencia es otro,
así que el offset es distinto y se mide aparte con el picker.
"""

import time

from .. import input as inp
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_region

LUCK_TEMPLATES = [
    ITEMS_DIR / "blue_luck.png",
    ITEMS_DIR / "green_luck.png",
    ITEMS_DIR / "yellow_luck.png",
    ITEMS_DIR / "purple_luck.png",
]

# Permisivo como los greens de fase 1.
LUCK_THRESHOLD = 0.70

# Offset desde el right-click hasta "Consume All".
# Sacado del bot viejo (misma res 4K): main_old.py -> pyautogui.move(20, 125).
CONSUME_ALL_OFFSET = (20, 125)

SLEEP_AFTER_RIGHT_CLICK = 0.8   # que el tooltip se quite y abra el menú
SLEEP_HOVER = 0.3               # asentar cursor sobre "Consume All"
SLEEP_AFTER_CONSUME = 1.5       # que el stack desaparezca antes del siguiente


def find_luck(template) -> tuple[int, int] | None:
    return vision.find(template, region=get_region("INVENTORY_AREA"),
                       threshold=LUCK_THRESHOLD)


def consume_all_at(point: tuple[int, int]) -> None:
    inp.move_to(point)
    time.sleep(0.25)
    inp.right_click(point)
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    inp.move_rel(*CONSUME_ALL_OFFSET)
    time.sleep(SLEEP_HOVER)
    inp.click_here()


def run() -> bool:
    if CONSUME_ALL_OFFSET is None:
        print("[fase2] CONSUME_ALL_OFFSET sin medir. Usá el picker y completá el offset.")
        return False

    consumed = False
    for tpl in LUCK_TEMPLATES:
        spot = find_luck(tpl)
        if not spot:
            continue
        print(f"[fase2] {tpl.name} en {spot}, Consume All...")
        consume_all_at(spot)
        time.sleep(SLEEP_AFTER_CONSUME)
        consumed = True

    if not consumed:
        print("[fase2] no hay esencia de suerte. Nada que hacer.")
    return consumed

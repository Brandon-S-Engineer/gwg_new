"""Abrir Lucky Red Bags del inventario: right-click → "Use All", igual que
fase1 con los greens, pero sin identificar ni salvage después — solo hay
que abrirlas. Tiempos propios (un poco más rápidos que fase1) para calibrar
aparte.

Comando suelto, NO está enganchado a TASKS ni FINAL_TASKS:

    py -m bot open_bags

Item necesario (capturar con el picker, pestaña de items):
    lucky_red_bag - ícono de la bolsa en el inventario
"""

import time

from .. import config
from .. import input as inp
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_region
from ..regions import Region
from .phase1_salvage_greens import USE_ALL, USE_ALL_THRESHOLD

LUCKY_RED_BAG = ITEMS_DIR / "lucky_red_bag.png"
BAG_THRESHOLD = 0.85

MAX_PASSES = 40  # tope de seguridad, no loop infinito

SLEEP_BEFORE_RIGHT_CLICK = schedule.OPEN_BAGS_BEFORE_RIGHT_CLICK
SLEEP_AFTER_RIGHT_CLICK = schedule.OPEN_BAGS_AFTER_RIGHT_CLICK
SLEEP_HOVER_USE_ALL = schedule.OPEN_BAGS_HOVER_USE_ALL
SLEEP_AFTER_OPEN = schedule.OPEN_BAGS_AFTER_OPEN

# Mismo patrón de menú que fase1 (right-click → mover al menú → "Use All").
MENU_DISMISS_OFFSET = (16, 88)
MENU_REGION_DX = -10
MENU_REGION_DY = 0
MENU_REGION_W = 500
MENU_REGION_H = 360


def find_bag() -> tuple[int, int] | None:
    return vision.find(LUCKY_RED_BAG, region=get_region("INVENTORY_AREA"),
                       threshold=BAG_THRESHOLD)


def _menu_region(point: tuple[int, int]) -> Region:
    x = max(0, point[0] + MENU_REGION_DX)
    y = max(0, point[1] + MENU_REGION_DY)
    w = min(MENU_REGION_W, config.SCREEN_WIDTH - x)
    h = min(MENU_REGION_H, config.SCREEN_HEIGHT - y)
    return Region(x, y, w, h)


def _open_at(point: tuple[int, int]) -> bool:
    inp.move_to(point)
    time.sleep(SLEEP_BEFORE_RIGHT_CLICK)
    inp.right_click(point)
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    inp.move_rel(*MENU_DISMISS_OFFSET)
    time.sleep(SLEEP_HOVER_USE_ALL)

    btn = vision.wait_for(USE_ALL, region=_menu_region(point),
                          timeout=1.5, threshold=USE_ALL_THRESHOLD)
    if not btn:
        print("[open_bags] no apareció 'Use All', abortando (no clickeo a ciegas)")
        return False
    inp.click(btn)
    return True


def run() -> int:
    """Abre todas las lucky red bags del inventario. Devuelve cuántas abrió."""
    count = 0
    for _ in range(MAX_PASSES):
        spot = find_bag()
        if not spot:
            break
        print(f"[open_bags] bolsa en {spot}, Use All...")
        if not _open_at(spot):
            break
        time.sleep(SLEEP_AFTER_OPEN)
        count += 1
    print(f"[open_bags] {count} bolsa(s) abierta(s)")
    return count

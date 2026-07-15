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

import cv2

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

# Si el "Use All" no aparece tras clickear una bolsa recién abierta, es
# porque el reescaneo la volvió a encontrar a ella misma (el slot todavía
# no se vació del todo). Excluir esa posición de la siguiente búsqueda.
SAME_SPOT_RADIUS = 40

MAX_PASSES = 40  # tope de seguridad, no loop infinito

SLEEP_BEFORE_RIGHT_CLICK = schedule.OPEN_BAGS_BEFORE_RIGHT_CLICK
SLEEP_AFTER_RIGHT_CLICK = schedule.OPEN_BAGS_AFTER_RIGHT_CLICK
SLEEP_HOVER_USE_ALL = schedule.OPEN_BAGS_HOVER_USE_ALL
SLEEP_AFTER_OPEN = schedule.OPEN_BAGS_AFTER_OPEN

# Mover el cursor en horizontal puro (sin bajar) para no tapar el texto de
# "Use All" con el ícono del cursor al pasar por encima camino al menú.
MENU_DISMISS_OFFSET = (120, 0)
MENU_REGION_DX = -10
MENU_REGION_DY = 0
MENU_REGION_W = 500
MENU_REGION_H = 360


def find_bag(exclude: tuple[int, int] | None = None) -> tuple[int, int] | None:
    """Busca una bolsa. Si `exclude` viene dado, descarta matches muy cerca
    de esa posición (la última abierta) e iterando busca la siguiente,
    igual que el fallback de fase1 en el banco."""
    region = get_region("INVENTORY_AREA")
    if exclude is None:
        return vision.find(LUCKY_RED_BAG, region=region, threshold=BAG_THRESHOLD)

    screen = vision.capture_screen(region)
    tpl = cv2.imread(str(LUCKY_RED_BAG), 0)
    if tpl is None:
        raise FileNotFoundError(LUCKY_RED_BAG)
    th, tw = tpl.shape[:2]
    result = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)

    for _ in range(10):
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < BAG_THRESHOLD:
            return None
        abs_x = region.x + max_loc[0] + tw // 2
        abs_y = region.y + max_loc[1] + th // 2

        if abs(abs_x - exclude[0]) <= SAME_SPOT_RADIUS and abs(abs_y - exclude[1]) <= SAME_SPOT_RADIUS:
            print(f"[open_bags] match en ({abs_x},{abs_y}) es la misma de recién, descartando")
            x0 = max(0, max_loc[0] - tw // 2)
            y0 = max(0, max_loc[1] - th // 2)
            x1 = min(result.shape[1], max_loc[0] + tw // 2 + 1)
            y1 = min(result.shape[0], max_loc[1] + th // 2 + 1)
            result[y0:y1, x0:x1] = 0
            continue

        return (abs_x, abs_y)

    return None


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
    last_spot = None
    for _ in range(MAX_PASSES):
        spot = find_bag(exclude=last_spot)
        if not spot:
            break
        print(f"[open_bags] bolsa en {spot}, Use All...")
        if not _open_at(spot):
            break
        last_spot = spot
        time.sleep(SLEEP_AFTER_OPEN)
        count += 1
    print(f"[open_bags] {count} bolsa(s) abierta(s)")
    return count

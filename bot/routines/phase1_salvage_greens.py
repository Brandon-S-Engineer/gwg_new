"""Fase 1: identificar greens y hacer salvage con Rune Crafter.

Flujo:
  1. Buscar green.png en INVENTORY_AREA. Si hay → "Use All".
  2. Si no, buscar en BANK_AREA → doble-click stack → recheck inventario.
  3. Salvage con Rune Crafter (template match del kit en el inv).
  4. Clicks de confirm (con fallbacks).
"""

import time

from .. import input as inp
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point, get_region

GREEN = ITEMS_DIR / "green.png"

# Threshold permisivo para greens — el bot viejo usaba 0.70 y funcionaba.
# Si captura/gamma del VM difiere ligeramente, 0.80 default es demasiado estricto.
GREEN_THRESHOLD = 0.70

SLEEP_AFTER_IDENTIFY = 4.0
SLEEP_AFTER_SALVAGE = 6.0
SLEEP_AFTER_BANK_DOUBLECLICK = 1.0

SLEEP_AFTER_RIGHT_CLICK = 0.8  # que el tooltip del item se quite
SLEEP_HOVER_USE_ALL = 0.3  # asentar cursor sobre "Use All" antes de clickear

# Offset relativo desde el right-click hasta "Use All", medido por el usuario
# con el picker (puntos 673,226 → 718,407 → diff 45,181).
USE_ALL_OFFSET = (45, 181)

CONFIRM_POINTS = [
    "rune_crafter_confirm_button",
    "rune_crafter_confirm_button_1",
    "rune_crafter_confirm_button_2",
    "rune_crafter_confirm_button_3",
    "rune_crafter_confirm_button_4",
    "rune_crafter_confirm_button_5",
    "rune_crafter_confirm_button_6",
]


def find_green_in_inventory() -> tuple[int, int] | None:
    return vision.find(GREEN, region=get_region("INVENTORY_AREA"),
                       threshold=GREEN_THRESHOLD)


def find_green_in_bank() -> tuple[int, int] | None:
    return vision.find(GREEN, region=get_region("BANK_AREA"),
                       threshold=GREEN_THRESHOLD)


def use_all_at(point: tuple[int, int]) -> None:
    inp.move_to(point)
    time.sleep(0.25)
    inp.right_click(point)
    pos_after_rc = inp._cursor_pos()
    print(f"[fase1] right-click en green {point}; cursor real: {pos_after_rc}")
    expected = (pos_after_rc[0] + USE_ALL_OFFSET[0],
                pos_after_rc[1] + USE_ALL_OFFSET[1])
    print(f"[fase1] use_all target esperado: {expected} (offset {USE_ALL_OFFSET})")
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    inp.DEBUG_ABS_MOVE = True
    inp.move_rel(*USE_ALL_OFFSET)
    inp.DEBUG_ABS_MOVE = False
    pos_after_move = inp._cursor_pos()
    print(f"[fase1] cursor tras move_rel: {pos_after_move}")
    time.sleep(SLEEP_HOVER_USE_ALL)
    inp.click_here()


def salvage_with_rune_crafter() -> bool:
    inp.right_click(get_point("rune_crafter"))
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    inp.click(get_point("rune_crafter_salvage_green"))
    time.sleep(0.5)

    for name in CONFIRM_POINTS:
        inp.click(get_point(name))
        time.sleep(0.05)
    return True


def run() -> bool:
    print("[fase1] buscando greens en inventario...")
    spot = find_green_in_inventory()

    if not spot:
        print("[fase1] no hay en inv, buscando en banco...")
        bank_spot = find_green_in_bank()
        if not bank_spot:
            print("[fase1] no hay greens ni en inv ni en banco. Nada que hacer.")
            return False
        print(f"[fase1] green en banco {bank_spot}, doble-click...")
        inp.double_click(bank_spot)
        time.sleep(SLEEP_AFTER_BANK_DOUBLECLICK)
        spot = find_green_in_inventory()
        if not spot:
            print("[fase1] tras mover, no apareció en inv. Aborto.")
            return False

    print(f"[fase1] green en inv {spot}, Use All...")
    use_all_at(spot)
    time.sleep(SLEEP_AFTER_IDENTIFY)

    print("[fase1] salvage con rune_crafter...")
    if not salvage_with_rune_crafter():
        return False
    time.sleep(SLEEP_AFTER_SALVAGE)

    print("[fase1] OK")
    return True

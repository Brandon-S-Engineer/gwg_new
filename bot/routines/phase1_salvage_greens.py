"""Fase 1: identificar greens y hacer salvage con Rune Crafter.

Flujo:
  1. Buscar green.png en INVENTORY_AREA. Si hay → "Use All".
  2. Si no, buscar en BANK_AREA → doble-click stack → recheck inventario.
  3. Salvage con Rune Crafter (template match del kit en el inv).
  4. Click en "Accept" por template (salvage.click_accept).
"""

import time

import cv2
import numpy as np

from .. import config
from .. import dialogs
from .. import input as inp
from .. import salvage
from .. import vision
from ..config import ITEMS_DIR, NO_GREENS
from ..coords_loader import get_point, get_region
from ..regions import Region

GREEN = ITEMS_DIR / "green.png"
GREEN_LUCK = ITEMS_DIR / "green_luck.png"
GREEN_LUCK_THRESHOLD = 0.80

# Template recapturado en el VM: green real matchea ~0.99, ruido sin greens
# ~0.62. 0.85 separa con margen de sobra.
GREEN_THRESHOLD = 0.85

# "Use All" por imagen, igual que la venta hace "Sell at Trading Post".
# Capturar el template EN EL VM, recortado al texto. Si no aparece, abortar:
# NUNCA clickear a ciegas (un offset fijo puede caer en "Destroy").
USE_ALL = ITEMS_DIR / "use_all.png"
USE_ALL_THRESHOLD = 0.85

SLEEP_AFTER_IDENTIFY = 8.0  # esperar a que abra/procese el unidentified green gear
SLEEP_AFTER_SALVAGE = 9.0
SLEEP_AFTER_BANK_DOUBLECLICK = 3.0  # que la verde aparezca en el inv antes de re-escanear

SLEEP_AFTER_RIGHT_CLICK = 0.8  # que el tooltip del item se quite
SLEEP_HOVER_USE_ALL = 0.3  # asentar cursor sobre "Use All" antes de clickear

# Sacar el cursor del item hacia el menú: quita el tooltip de hover.
MENU_DISMISS_OFFSET = (16, 88)

# Región del menú abajo-derecha del right-click (6 items, texto largo).
MENU_REGION_DX = -10
MENU_REGION_DY = 0
MENU_REGION_W = 500
MENU_REGION_H = 360


def find_green_in_inventory() -> tuple[int, int] | None:
    return vision.find(GREEN, region=get_region("INVENTORY_AREA"),
                       threshold=GREEN_THRESHOLD)


def find_green_in_bank() -> tuple[int, int] | None:
    """Busca green gear en banco, saltando posiciones que sean green luck."""
    region = get_region("BANK_AREA")
    screen = vision.capture_screen(region)
    tpl = cv2.imread(str(GREEN), 0)
    if tpl is None:
        raise FileNotFoundError(GREEN)
    th, tw = tpl.shape[:2]
    result = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)

    for _ in range(15):
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < GREEN_THRESHOLD:
            return None

        abs_x = region.x + max_loc[0] + tw // 2
        abs_y = region.y + max_loc[1] + th // 2

        # Verificar que no sea luck en esa posición exacta
        slot = Region(abs_x - 25, abs_y - 25, 50, 50)
        if vision.is_present(GREEN_LUCK, region=slot,
                             threshold=GREEN_LUCK_THRESHOLD, color=True):
            print(f"[fase1] bank: spot ({abs_x},{abs_y}) es luck, saltando")
            # Enmascarar ese slot y buscar de nuevo
            x0 = max(0, max_loc[0] - tw // 2)
            y0 = max(0, max_loc[1] - th // 2)
            x1 = min(result.shape[1], max_loc[0] + tw // 2 + 1)
            y1 = min(result.shape[0], max_loc[1] + th // 2 + 1)
            result[y0:y1, x0:x1] = 0
            continue

        print(f"[vision] {GREEN.name}: max_val={max_val:.3f} ok (banco)")
        return (abs_x, abs_y)

    return None


def _menu_region(point: tuple[int, int]) -> Region:
    x = max(0, point[0] + MENU_REGION_DX)
    y = max(0, point[1] + MENU_REGION_DY)
    w = min(MENU_REGION_W, config.SCREEN_WIDTH - x)
    h = min(MENU_REGION_H, config.SCREEN_HEIGHT - y)
    return Region(x, y, w, h)


def use_all_at(point: tuple[int, int]) -> bool:
    """Right-click sobre el green y clickea 'Use All' por imagen. True si lo hizo.

    Si 'Use All' no aparece (menú distinto, item movido), aborta sin clickear:
    nunca a ciegas, para no pegarle a 'Destroy'.
    """
    inp.move_to(point)
    time.sleep(0.25)
    inp.right_click(point)
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    # Sacar el cursor del item hacia el menú: quita el tooltip de hover.
    inp.move_rel(*MENU_DISMISS_OFFSET)
    time.sleep(SLEEP_HOVER_USE_ALL)

    btn = vision.wait_for(USE_ALL, region=_menu_region(point),
                          timeout=1.5, threshold=USE_ALL_THRESHOLD)
    if not btn:
        print("[fase1] no apareció 'Use All', abortando (no clickeo a ciegas)")
        return False
    inp.click(btn)
    return True


def salvage_with_rune_crafter() -> bool:
    inp.right_click(get_point("rune_crafter"))
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    inp.click(get_point("rune_crafter_salvage_green"))
    time.sleep(0.5)

    return salvage.click_accept()


def run() -> bool:
    print("[fase1] buscando greens en inventario...")
    spot = find_green_in_inventory()

    if not spot:
        print("[fase1] no hay en inv, buscando en banco...")
        bank_spot = find_green_in_bank()
        if not bank_spot:
            print("[fase1] no hay greens ni en inv ni en banco. Nada que hacer.")
            return NO_GREENS
        print(f"[fase1] green en banco {bank_spot}, doble-click...")
        inp.double_click(bank_spot)
        time.sleep(SLEEP_AFTER_BANK_DOUBLECLICK)
        spot = find_green_in_inventory()
        if not spot:
            print("[fase1] tras mover, no apareció en inv. Aborto.")
            return False

    print(f"[fase1] green en inv {spot}, Use All...")
    if not use_all_at(spot):
        return False
    dialogs.sleep_safe(SLEEP_AFTER_IDENTIFY)

    print("[fase1] salvage con rune_crafter...")
    if not salvage_with_rune_crafter():
        return False
    dialogs.sleep_safe(SLEEP_AFTER_SALVAGE)

    print("[fase1] OK")
    return True

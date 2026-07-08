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
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR, NO_GREENS
from ..coords_loader import get_point, get_region
from ..regions import Region

GREEN = ITEMS_DIR / "green.png"
LUCK_TEMPLATES = [
    ITEMS_DIR / "blue_luck.png",
    ITEMS_DIR / "green_luck.png",
    ITEMS_DIR / "yellow_luck.png",
    ITEMS_DIR / "purple_luck.png",
]
LUCK_THRESHOLD = 0.80

# Template recapturado en el VM: green real matchea ~0.99, ruido sin greens
# ~0.62. 0.85 separa con margen de sobra.
GREEN_THRESHOLD = 0.85

# El template se capturó desde el inventario; en el banco el render del
# ícono es ligeramente distinto (otra escala/zoom de esa vista) y el score
# sale sistemáticamente más bajo. La mayoría igual pasa 0.85, pero quedaban
# 3-5 items pegados justo debajo, sin que ni el fast path ni el fallback
# anti-luck los rescataran (ambos cortaban en 0.85 antes de llegar ahí).
# Solo para banco; NO tocar GREEN_THRESHOLD (inventario funciona perfecto).
BANK_GREEN_THRESHOLD = 0.75

# "Use All" por imagen, igual que la venta hace "Sell at Trading Post".
# Capturar el template EN EL VM, recortado al texto. Si no aparece, abortar:
# NUNCA clickear a ciegas (un offset fijo puede caer en "Destroy").
USE_ALL = ITEMS_DIR / "use_all.png"
USE_ALL_THRESHOLD = 0.85

# Tiempos centralizados en schedule.py para calibrarlos en un solo lugar.
SLEEP_BEFORE_RIGHT_CLICK = schedule.PHASE1_BEFORE_RIGHT_CLICK
SLEEP_AFTER_RIGHT_CLICK = schedule.PHASE1_AFTER_RIGHT_CLICK
SLEEP_HOVER_USE_ALL = schedule.PHASE1_HOVER_USE_ALL
SLEEP_AFTER_SALVAGE_OPTION = schedule.PHASE1_AFTER_SALVAGE_OPTION
SLEEP_AFTER_IDENTIFY = schedule.PHASE1_AFTER_IDENTIFY
SLEEP_AFTER_SALVAGE = schedule.PHASE1_AFTER_SALVAGE
SLEEP_AFTER_BANK_DOUBLECLICK = schedule.PHASE1_AFTER_BANK_DOUBLECLICK

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

    # Caso normal: encontró gear directamente
    spot = vision.find(GREEN, region=region, threshold=BANK_GREEN_THRESHOLD)
    if spot:
        return spot

    # Fallback: puede haber luck tapando; busca iterando y excluyendo luck
    print("[fase1] bank: find normal falló, buscando con exclusión de luck...")
    screen = vision.capture_screen(region)
    tpl = cv2.imread(str(GREEN), 0)
    if tpl is None:
        raise FileNotFoundError(GREEN)
    th, tw = tpl.shape[:2]
    result = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)

    for _ in range(15):
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < BANK_GREEN_THRESHOLD:
            return None

        abs_x = region.x + max_loc[0] + tw // 2
        abs_y = region.y + max_loc[1] + th // 2

        # Verificar que no sea ningún tipo de luck en esa posición
        slot = Region(abs_x - 25, abs_y - 25, 50, 50)
        is_luck = any(vision.is_present(lk, region=slot,
                                        threshold=LUCK_THRESHOLD, color=True)
                      for lk in LUCK_TEMPLATES)
        if is_luck:
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
    time.sleep(SLEEP_BEFORE_RIGHT_CLICK)
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
    time.sleep(SLEEP_AFTER_SALVAGE_OPTION)

    return salvage.click_accept()


def recover() -> bool:
    """Recovery tras el diálogo de conn_error (dialogs.check_conn_error).

    Este error sale seguido cuando el inventario se satura de greens sin
    identificar. Si hay, los identifica primero (Use All) y espera; si no
    hay, corre el salvage directo (puede haber verdes ya identificados
    esperando el rune_crafter).
    """
    spot = find_green_in_inventory()
    if spot:
        print(f"[fase1] recovery: unidentified gear en inv {spot}, Use All...")
        if use_all_at(spot):
            time.sleep(SLEEP_AFTER_IDENTIFY)
    else:
        print("[fase1] recovery: nada sin identificar en inv, salvage directo...")

    print("[fase1] recovery: salvage con rune_crafter...")
    ok = salvage_with_rune_crafter()
    time.sleep(SLEEP_AFTER_SALVAGE)
    return ok


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

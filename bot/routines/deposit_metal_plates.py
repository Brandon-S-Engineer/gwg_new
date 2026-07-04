"""Depositar materiales directo al depósito de materiales (sin pasar por TP).

Misma lógica que phase2_consume_luck (right-click → cerrar tooltip → template
match del botón → click), adaptada: en vez de "Consume All" busca
"Deposit Material" en el menú contextual.

Flujo por stack:
  1. right-click sobre el material (abre el menú contextual).
  2. mover el cursor hacia el menú (abajo-derecha) → quita el tooltip de hover
     que si no taparía el botón.
  3. template match de deposit_material.png en la región del menú.
  4. click en el botón.

"Deposit Material" vacía un solo stack; se repite hasta MAX_PASSES_PER_ITEM
por si hay más de un stack del mismo material.
"""

import time

from .. import config
from .. import input as inp
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_region
from ..regions import Region

RECLAIMED_METAL_PLATES = ITEMS_DIR / "reclaimed_metal_plates.png"

MATERIALS = [RECLAIMED_METAL_PLATES]

DEPOSIT_MATERIAL = ITEMS_DIR / "deposit_material.png"

ITEM_THRESHOLD = 0.85
DEPOSIT_THRESHOLD = 0.78

# Sacar el cursor del item hacia el menú: quita el tooltip de hover.
# Mismo offset que fase2 (misma clase de menú contextual).
DISMISS_OFFSET = (20, 125)

# Región del menú respecto al right-click: abre abajo-derecha, no muy lejos.
MENU_REGION_DX = -10
MENU_REGION_DY = 0
MENU_REGION_W = 420
MENU_REGION_H = 280

MAX_PASSES_PER_ITEM = 3

# Tiempos centralizados en schedule.py para calibrarlos en un solo lugar.
SLEEP_BEFORE_RIGHT_CLICK = schedule.DEPOSIT_BEFORE_RIGHT_CLICK
SLEEP_AFTER_RIGHT_CLICK = schedule.DEPOSIT_AFTER_RIGHT_CLICK
SLEEP_AFTER_DISMISS = schedule.DEPOSIT_AFTER_DISMISS
SLEEP_AFTER_DEPOSIT = schedule.DEPOSIT_AFTER_DEPOSIT


def find_material(template) -> tuple[int, int] | None:
    return vision.find(template, region=get_region("INVENTORY_AREA"),
                       threshold=ITEM_THRESHOLD)


def _menu_region(point: tuple[int, int]) -> Region:
    """Caja del menú abajo-derecha del click, clampeada a la pantalla."""
    x = max(0, point[0] + MENU_REGION_DX)
    y = max(0, point[1] + MENU_REGION_DY)
    w = min(MENU_REGION_W, config.SCREEN_WIDTH - x)
    h = min(MENU_REGION_H, config.SCREEN_HEIGHT - y)
    return Region(x, y, w, h)


def deposit_at(point: tuple[int, int]) -> bool:
    """True si depositó (apareció el botón); False si fue falso positivo."""
    inp.move_to(point)
    time.sleep(SLEEP_BEFORE_RIGHT_CLICK)
    inp.right_click(point)
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)

    # Sacar el cursor del item hacia el menú: quita el tooltip de hover.
    inp.move_rel(*DISMISS_OFFSET)
    time.sleep(SLEEP_AFTER_DISMISS)

    btn = vision.wait_for(DEPOSIT_MATERIAL, region=_menu_region(point),
                          timeout=1.0, threshold=DEPOSIT_THRESHOLD)
    if btn:
        inp.click(btn)
        return True

    # Sin botón = no se abrió menú = el find fue falso positivo. No clickear.
    print("[deposit_metal_plates] sin botón Deposit Material: falso positivo, no clickeo")
    return False


def run(materials=None) -> bool:
    if materials is None:
        materials = MATERIALS
    deposited = False
    for tpl in materials:
        for _ in range(MAX_PASSES_PER_ITEM):
            spot = find_material(tpl)
            if not spot:
                break
            print(f"[deposit_metal_plates] {tpl.name} en {spot}, Deposit Material...")
            if not deposit_at(spot):
                break  # falso positivo persistente: no reintentar este material
            time.sleep(SLEEP_AFTER_DEPOSIT)
            deposited = True

    if not deposited:
        print("[deposit_metal_plates] nada que depositar.")
    return deposited

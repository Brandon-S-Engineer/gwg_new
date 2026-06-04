"""Fase 2: consumir Esencia de Suerte (puro estorbo de inventario).

Las 4 tiers (blue/green/yellow/purple) se limpian con right-click → "Consume All".

Flujo por stack:
  1. right-click sobre la esencia (abre el menú contextual).
  2. mover el cursor hacia el menú (abajo-derecha) → quita el tooltip de hover
     que si no taparía el botón.
  3. template match de consume_all.png en la región del menú.
  4. click en el botón; si no matchea, click donde quedó el cursor (offset fijo).

"Consume All" vacía un solo stack. Blue suele tener 2+ stacks, así que cada
tier se consume hasta que no quede ninguno (hasta MAX_PASSES_PER_TIER).
"""

import time

from .. import config
from .. import input as inp
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_region
from ..regions import Region

LUCK_TEMPLATES = [
    ITEMS_DIR / "blue_luck.png",
    ITEMS_DIR / "green_luck.png",
    ITEMS_DIR / "yellow_luck.png",
    ITEMS_DIR / "purple_luck.png",
]

CONSUME_ALL = ITEMS_DIR / "consume_all.png"

# Match en COLOR. En gris no se separa: en este VM (gamma) un elemento de UI
# que no es suerte matchea ~0.85, igual que la suerte real. El color (único
# diferenciador entre las 4 tiers) sí los distingue. Escala distinta a gris;
# afinar con el max_val que imprime vision.
LUCK_THRESHOLD = 0.70
# El botón es texto fijo; estricto para no matchear otro UI.
CONSUME_ALL_THRESHOLD = 0.90

# Movimiento desde el right-click hacia el menú. Cumple doble función:
#   - saca el cursor del item → quita el tooltip de hover antes del matching;
#   - si el template no matchea, es el offset ciego (cae sobre "Consume All").
# Del bot viejo (misma res 4K): main_old.py -> pyautogui.move(20, 125).
CONSUME_ALL_OFFSET = (20, 125)

# Región del menú respecto al right-click: abre abajo-derecha, no muy lejos.
MENU_REGION_DX = -10
MENU_REGION_DY = 0
MENU_REGION_W = 420
MENU_REGION_H = 280

# Blue sobra y llena 2+ stacks; el resto rara vez pasa de uno. Corta loops
# si un consume falla y el stack se queda.
MAX_PASSES_PER_TIER = 3

SLEEP_AFTER_RIGHT_CLICK = 0.8   # que abra el menú (NO tocar: es el right-click + bajar que quita el hover)
SLEEP_AFTER_DISMISS = 0.1       # tooltip ya se fue al bajar; clickear cuanto antes
SLEEP_AFTER_CONSUME = 0.4       # mínimo para que el stack desaparezca, y siguiente


def find_luck(template) -> tuple[int, int] | None:
    # color=True: en gris la basura matchea tan alto como la suerte real.
    return vision.find(template, region=get_region("INVENTORY_AREA"),
                       threshold=LUCK_THRESHOLD, color=True)


def _menu_region(point: tuple[int, int]) -> Region:
    """Caja del menú abajo-derecha del click, clampeada a la pantalla."""
    x = max(0, point[0] + MENU_REGION_DX)
    y = max(0, point[1] + MENU_REGION_DY)
    w = min(MENU_REGION_W, config.SCREEN_WIDTH - x)
    h = min(MENU_REGION_H, config.SCREEN_HEIGHT - y)
    return Region(x, y, w, h)


def consume_all_at(point: tuple[int, int]) -> None:
    inp.move_to(point)
    time.sleep(0.08)
    inp.right_click(point)
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)

    # Sacar el cursor del item hacia el menú: quita el tooltip de hover.
    inp.move_rel(*CONSUME_ALL_OFFSET)
    time.sleep(SLEEP_AFTER_DISMISS)

    btn = vision.wait_for(CONSUME_ALL, region=_menu_region(point),
                          timeout=1.0, threshold=CONSUME_ALL_THRESHOLD)
    if btn:
        inp.click(btn)
        return

    # Sin match: el cursor ya está sobre el offset, click acá.
    print("[fase2] botón Consume All no encontrado, click en offset fijo")
    inp.click_here()


def run() -> bool:
    consumed = False
    for tpl in LUCK_TEMPLATES:
        for _ in range(MAX_PASSES_PER_TIER):
            spot = find_luck(tpl)
            if not spot:
                break
            print(f"[fase2] {tpl.name} en {spot}, Consume All...")
            consume_all_at(spot)
            time.sleep(SLEEP_AFTER_CONSUME)
            consumed = True

    if not consumed:
        print("[fase2] no hay esencia de suerte. Nada que hacer.")
    return consumed

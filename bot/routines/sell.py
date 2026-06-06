"""Venta de materiales en el TP — venta instantánea al mejor comprador.

Genérico: sell_item("silk_scraps") busca el item, right-click → "Sell at
Trading Post" (template, como consume_all/accept) → panel de venta por coords.

NO sirve para ectos (se convierten a crystalline dust con silver_fed, futuro)
ni para lucent motes (otro flujo). Esos van aparte.
"""

import time

from .. import config
from .. import input as inp
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point, get_region
from ..regions import Region

SELL_AT_TP = ITEMS_DIR / "sell_at_tp.png"
SELL_AT_TP_THRESHOLD = 0.85
# Threshold del item. Como en fase 1, el gamma del VM puede pedir bajarlo;
# mirá el max_val que imprime vision.
ITEM_THRESHOLD = 0.80

# Offset para sacar el hover y acercarse al menú. Del bot viejo: move(16, 88)
# (cae sobre "Sell at Trading Post", el 3er spot). El template ajusta el click.
MENU_DISMISS_OFFSET = (16, 88)

# Región del menú abajo-derecha del right-click (6 items, texto largo).
MENU_REGION_DX = -10
MENU_REGION_DY = 0
MENU_REGION_W = 500
MENU_REGION_H = 360

SLEEP_AFTER_RIGHT_CLICK = 0.8   # que abra el menú
SLEEP_AFTER_DISMISS = 0.1       # tooltip ya se fue al bajar
SLEEP_PANEL = 1.5               # que abra el panel de venta del TP
SLEEP_STEP = 0.25               # entre clicks del panel
SLEEP_AFTER_LIST = 1.5          # que se procese el listado


def _menu_region(point: tuple[int, int]) -> Region:
    x = max(0, point[0] + MENU_REGION_DX)
    y = max(0, point[1] + MENU_REGION_DY)
    w = min(MENU_REGION_W, config.SCREEN_WIDTH - x)
    h = min(MENU_REGION_H, config.SCREEN_HEIGHT - y)
    return Region(x, y, w, h)


def _click_sell_at_tp(point: tuple[int, int]) -> bool:
    inp.right_click(point)
    time.sleep(SLEEP_AFTER_RIGHT_CLICK)
    # Sacar el cursor del item hacia el menú: quita el tooltip de hover.
    inp.move_rel(*MENU_DISMISS_OFFSET)
    time.sleep(SLEEP_AFTER_DISMISS)

    btn = vision.wait_for(SELL_AT_TP, region=_menu_region(point),
                          timeout=1.5, threshold=SELL_AT_TP_THRESHOLD)
    if not btn:
        print("[sell] no apareció 'Sell at Trading Post'")
        return False
    inp.click(btn)
    return True


def sell_item(name: str) -> bool:
    """Vende un stack de `name` (instantáneo al mejor comprador). True si lo hizo."""
    tpl = ITEMS_DIR / f"{name}.png"
    spot = vision.find(tpl, region=get_region("INVENTORY_AREA"),
                       threshold=ITEM_THRESHOLD)
    if not spot:
        print(f"[sell] no hay {name} en inventario")
        return False

    print(f"[sell] {name} en {spot}, vendiendo...")
    if not _click_sell_at_tp(spot):
        return False

    time.sleep(SLEEP_PANEL)
    inp.click(get_point("sellers_list"))      # seleccionar venta al comprador
    time.sleep(SLEEP_STEP)
    inp.click(get_point("maximum_amount"))    # cantidad máxima
    time.sleep(SLEEP_STEP)
    inp.click(get_point("list_item"))         # listar / vender
    time.sleep(SLEEP_AFTER_LIST)
    print(f"[sell] {name} listado")
    return True

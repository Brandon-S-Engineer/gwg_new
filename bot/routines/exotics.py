"""Limpiar exotics acumulados: vender los N más caros en el TP, luego
salvage del resto por posición con silver_fed.

Portado del bot viejo (`sell_most_expensive_exotics` + `salvage_restant_exotics`
en reference_old/main_old.py), con un cambio: en vez de clickear un número
fijo de slots a ciegas para el salvage, usamos el Accept por imagen y
paramos en cuanto no aparece — así no importa si hay menos de MAX_SLOTS
exotics restantes.

Ojo: este Accept es un botón DISTINTO al de salvage.click_accept (ese sale
del menú contextual del kit en fase1/fase3). El salvage por posición arma
el kit y clickea directo sobre el item, y ese diálogo usa su propio template
(accept_salvage.png) y su propia región (EXOTIC_ACCEPT_REGION).

Corre standalone en FINAL_TASKS, DESPUÉS de deposit_metal_plates (al mero
final de todo). NO va durante las esperas de craft_essence: el
procesamiento de luck traba directamente el Trading Post, así que mezclarlo
ahí rompía la venta. Por lo mismo, antes de tocar nada del TP se resetea la
vista con las teclas m/o/o/m (abrir mapa, TP, TP, mapa) y se navega a la
sección de Trading Post — el crafteo puede haber dejado esa vista rara.

Flujo:
  1. Reset de vista: teclas m, o, o, m → click en la sección de Trading Post.
  2. Compactar inventario (así los exotics quedan en las primeras posiciones
     tanto para el slot "más caro" del TP como para el grid de salvage).
  3. Pestaña "Sell" del TP, ordenar por precio, vender el slot top TOP_N veces
     (cada venta hace subir al siguiente más caro a esa posición).
  4. Armar el silver_fed en modo "Use" (cursor de salvage) y recorrer el grid
     fijo de slots (post-compact), salvage + Accept por imagen; para en el
     primer slot vacío (Accept no aparece).
  5. Depositar los globs of dark matter que soltó el salvage (misma lógica
     que deposit_metal_plates: right-click → template del botón → click).

Coordenadas necesarias (agregar con el picker, ya tienen placeholder):
    tp_section            - sección/pestaña de Trading Post tras el reset
    sell_items_tab        - pestaña "Sell" del panel del TP
    sell_sort_price        - columna "Price" para ordenar (se clickea 2 veces)
    sell_top_slot           - primer/top item de la lista ordenada
    sell_top_confirm_1      - click para confirmar la venta del top slot
    sell_top_confirm_2      - 2do click de confirmar (nombres largos bajan
                              el botón; se clickean las dos posiciones)
    exotic_slot_1..20      - grid de slots del inventario post-compact, para
                              el barrido de salvage

Región necesaria (agregar con el picker):
    EXOTIC_ACCEPT_REGION - caja donde sale el Accept del salvage-por-click

Item necesario (capturar con el picker, pestaña de items):
    accept_salvage - botón Accept del diálogo que sale al salvage-por-click
                     (distinto al accept.png del menú contextual)
"""

import time

from .. import input as inp
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point, get_region
from . import deposit_metal_plates, store_luck

TOP_N = 5
MAX_SLOTS = 20
SLOT_NAMES = [f"exotic_slot_{i}" for i in range(1, MAX_SLOTS + 1)]

# El Accept del salvage por posición (kit armado + click en item) es un
# botón DISTINTO al de salvage.click_accept (ese es del menú contextual del
# kit). Mismo tipo de diálogo, misma columna, template propio.
ACCEPT_SALVAGE = ITEMS_DIR / "accept_salvage.png"
ACCEPT_SALVAGE_THRESHOLD = 0.85

SLEEP_AFTER_CLOSE = schedule.EXOTICS_AFTER_CLOSE
SLEEP_AFTER_TAB = schedule.EXOTICS_AFTER_TAB
SLEEP_AFTER_SORT = schedule.EXOTICS_AFTER_SORT
SLEEP_AFTER_SORT_FINAL = schedule.EXOTICS_AFTER_SORT_FINAL
SLEEP_AFTER_SELECT = schedule.EXOTICS_AFTER_SELECT
SLEEP_AFTER_SUCCESS = schedule.EXOTICS_AFTER_SUCCESS
SLEEP_AFTER_ARM_KIT = schedule.EXOTICS_AFTER_ARM_KIT
SLEEP_AFTER_SALVAGE_CLICK = schedule.EXOTICS_AFTER_SALVAGE_CLICK
SLEEP_AFTER_TP_SECTION = schedule.EXOTICS_AFTER_TP_SECTION


def _reset_tp_view():
    """m, o, o, m (igual patrón que setup.open_windows) para resetear la
    vista del TP tras el crafteo, y navegar a la sección de Trading Post."""
    import keyboard as _kb
    for key in ("m", "o", "o", "m"):
        _kb.press_and_release(key)
        time.sleep(schedule.SETUP_AFTER_KEYPRESS)
    inp.click(get_point("tp_section"))
    time.sleep(SLEEP_AFTER_TP_SECTION)


def _open_sell_sorted_by_price():
    inp.click(get_point("sell_close"))
    time.sleep(SLEEP_AFTER_CLOSE)
    inp.click(get_point("sell_items_tab"))
    time.sleep(SLEEP_AFTER_TAB)
    inp.click(get_point("sell_sort_price"))
    time.sleep(SLEEP_AFTER_SORT)
    inp.click(get_point("sell_sort_price"))
    time.sleep(SLEEP_AFTER_SORT_FINAL)


def _sell_top_one() -> bool:
    """Vende el item en el slot top (el más caro tras ordenar). Cada venta
    hace que el siguiente más caro suba a esa misma posición.

    Nombres largos empujan el botón de confirmar más abajo en el panel, así
    que sell_top_confirm_1 solo no alcanza para todos los items. Igual que
    el bot viejo: dos clicks, uno en cada posición posible."""
    inp.click(get_point("sell_top_slot"))
    time.sleep(SLEEP_AFTER_SELECT)
    inp.click(get_point("sell_top_confirm_1"))
    inp.click(get_point("sell_top_confirm_2"))
    time.sleep(SLEEP_AFTER_SUCCESS)
    inp.click(get_point("sell_close"))
    time.sleep(SLEEP_AFTER_CLOSE)
    return True


def _sell_top_exotics(n: int = TOP_N) -> None:
    print(f"[exotics] vendiendo los {n} más caros...")
    _open_sell_sorted_by_price()
    for _ in range(n):
        _sell_top_one()


def _arm_silver_fed():
    inp.right_click(get_point("silver_fed"))
    time.sleep(schedule.PHASE3_AFTER_RIGHT_CLICK)
    inp.click(get_point("silver_fed_use"))
    time.sleep(SLEEP_AFTER_ARM_KIT)


def _click_accept_salvage(timeout: float = 2.0) -> bool:
    btn = vision.wait_for(ACCEPT_SALVAGE, region=get_region("EXOTIC_ACCEPT_REGION"),
                          timeout=timeout, threshold=ACCEPT_SALVAGE_THRESHOLD)
    if btn:
        inp.click(btn)
        return True
    print("[exotics] accept_salvage no encontrado en la columna")
    return False


def _salvage_slot(point_name: str) -> bool:
    inp.click(get_point(point_name))
    time.sleep(SLEEP_AFTER_SALVAGE_CLICK)
    return _click_accept_salvage()


def _salvage_rest_exotics() -> None:
    _arm_silver_fed()
    for name in SLOT_NAMES:
        if not _salvage_slot(name):
            print(f"[exotics] {name} vacío, fin del salvage")
            break


def test_reset_view():
    """Solo el reset de vista (m,o,o,m + click tp_section), sin vender ni
    salvage. Para calibrar 'tp_section' sin arriesgar ventas.
    `py -m bot exotics view`"""
    _reset_tp_view()


def test_salvage_rest():
    """Solo compactar + salvage del resto (sin reset de vista ni vender los
    más caros). Para probar esta parte sola cuando ya no queden exotics
    caros que vender. `py -m bot exotics salvage`"""
    store_luck.compact()
    _salvage_rest_exotics()


def test_deposit_dark_matter():
    """Solo depositar globs of dark matter (sin lo demás). Misma lógica que
    deposit_metal_plates. `py -m bot exotics dark_matter`"""
    deposit_metal_plates.run(materials=[deposit_metal_plates.GLOBS_OF_DARK_MATTER])


def run():
    """Corre todo el flujo (`py -m bot exotics`)."""
    print("[exotics] limpieza de exotics...")
    _reset_tp_view()
    store_luck.compact()
    _sell_top_exotics()
    # Vender cambia el inventario (huecos donde estaban los vendidos): hay
    # que re-compactar antes del barrido por posición, si no el grid de
    # exotic_slot_N ya no coincide con lo que realmente queda.
    store_luck.compact()
    _salvage_rest_exotics()
    # El salvage de los exotics suelta dark matter: depositarlo al final.
    deposit_metal_plates.run(materials=[deposit_metal_plates.GLOBS_OF_DARK_MATTER])
    print("[exotics] OK")

"""Limpiar exotics acumulados: vender los N más caros en el TP, luego
salvage del resto por posición con silver_fed.

Portado del bot viejo (`sell_most_expensive_exotics` + `salvage_restant_exotics`
en reference_old/main_old.py), con un cambio: en vez de clickear un número
fijo de slots a ciegas para el salvage, usamos el Accept por imagen
(salvage.click_accept, igual que fase1/fase3) y paramos en cuanto no
aparece — así no importa si hay menos de MAX_SLOTS exotics restantes.

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

Coordenadas necesarias (agregar con el picker, ya tienen placeholder):
    tp_section            - sección/pestaña de Trading Post tras el reset
    sell_items_tab        - pestaña "Sell" del panel del TP
    sell_sort_price        - columna "Price" para ordenar (se clickea 2 veces)
    sell_top_slot           - primer/top item de la lista ordenada
    sell_top_confirm_1/2    - los 2 clicks para confirmar la venta del top slot
    exotic_slot_1..20      - grid de slots del inventario post-compact, para
                              el barrido de salvage
"""

import time

from .. import input as inp
from .. import salvage
from .. import schedule
from ..coords_loader import get_point
from . import store_luck

TOP_N = 5
MAX_SLOTS = 20
SLOT_NAMES = [f"exotic_slot_{i}" for i in range(1, MAX_SLOTS + 1)]

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
    hace que el siguiente más caro suba a esa misma posición."""
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


def _salvage_slot(point_name: str) -> bool:
    inp.click(get_point(point_name))
    time.sleep(SLEEP_AFTER_SALVAGE_CLICK)
    return salvage.click_accept()


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


def run():
    """Corre todo el flujo (`py -m bot exotics`)."""
    print("[exotics] limpieza de exotics...")
    _reset_tp_view()
    store_luck.compact()
    _sell_top_exotics()
    _salvage_rest_exotics()
    print("[exotics] OK")

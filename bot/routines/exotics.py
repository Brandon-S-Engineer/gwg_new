"""Limpiar exotics acumulados: vender los N más caros en el TP, luego
salvage del resto por posición con silver_fed.

Portado del bot viejo (`sell_most_expensive_exotics` + `salvage_restant_exotics`
en reference_old/main_old.py), con un cambio: en vez de clickear un número
fijo de slots a ciegas para el salvage, usamos el Accept por imagen
(salvage.click_accept, igual que fase1/fase3) y paramos en cuanto no
aparece — así no importa si hay menos de MAX_SLOTS exotics restantes.

Flujo:
  1. Compactar inventario (así los exotics quedan en las primeras posiciones
     tanto para el slot "más caro" del TP como para el grid de salvage).
  2. Pestaña "Sell" del TP, ordenar por precio, vender el slot top TOP_N veces
     (cada venta hace subir al siguiente más caro a esa posición).
  3. Armar el silver_fed en modo "Use" (cursor de salvage) y recorrer el grid
     fijo de slots (post-compact), salvage + Accept por imagen; para en el
     primer slot vacío (Accept no aparece).

Expone steps() como generator (1 yield por paso) para poder consumirse
durante las esperas de craft_essence, igual que sell_seals/sell_all_clean.

Coordenadas necesarias (agregar con el picker, ya tienen placeholder):
    sell_items_tab      - pestaña "Sell" del panel del TP
    sell_sort_price      - columna "Price" para ordenar (se clickea 2 veces)
    sell_top_slot         - primer/top item de la lista ordenada
    sell_top_confirm_1/2  - los 2 clicks para confirmar la venta del top slot
    exotic_slot_1..20    - grid de slots del inventario post-compact, para
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


def steps():
    """1 yield por paso: compactar, cada venta del top, cada salvage.
    Pensado para consumirse durante las esperas de craft_essence (mismo
    patrón que _sell_steps ahí): se pausa cuando se acaba el tiempo y
    retoma en la siguiente espera."""
    store_luck.compact()
    yield

    _open_sell_sorted_by_price()
    for _ in range(TOP_N):
        if not _sell_top_one():
            break
        yield

    _arm_silver_fed()
    for name in SLOT_NAMES:
        if not _salvage_slot(name):
            print(f"[exotics] {name} vacío, fin del salvage")
            break
        yield


def run():
    """Corre todo de una sentada (para probar suelto: `py -m bot exotics`)."""
    print("[exotics] limpieza de exotics...")
    for _ in steps():
        pass
    print("[exotics] OK")

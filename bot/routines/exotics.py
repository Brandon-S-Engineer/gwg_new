"""Limpiar exotics acumulados: vender los N más caros en el TP, luego
salvage del resto por posición con silver_fed.

Portado del bot viejo (`sell_most_expensive_exotics` + `salvage_restant_exotics`
en reference_old/main_old.py), con un cambio: en vez de clickear un número
fijo de slots a ciegas para el salvage, usamos el Accept por imagen y
paramos en cuanto no aparece — así no importa si hay menos de MAX_SLOTS
exotics restantes.

Ojo: este Accept es un botón DISTINTO al de salvage.click_accept (ese sale
del menú contextual del kit en fase1/fase3). El salvage por posición arma
el kit y clickea directo sobre el item, y ese diálogo usa accept_salvage.png
como template propio (misma columna/región que el otro, pero look distinto).

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
    sell_top_confirm_1      - click para confirmar la venta del top slot
    exotic_slot_1..20      - grid de slots del inventario post-compact, para
                              el barrido de salvage

Item necesario (capturar con el picker, pestaña de items):
    accept_salvage - botón Accept del diálogo que sale al salvage-por-click
                     (distinto al accept.png del menú contextual)
"""

import time

import cv2

from .. import config
from .. import input as inp
from .. import salvage
from .. import schedule
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_point
from . import store_luck

DEBUG_OUT_DIR = config.PROJECT_ROOT / "tools" / "debug_output"
DEBUG_FLOOR = 0.30   # piso bajo: queremos ver todo lo que exista arriba del ruido
DEBUG_MAX_MATCHES = 15
DEBUG_CROP_HALF = 50

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
    hace que el siguiente más caro suba a esa misma posición. Un solo click
    de confirmación; el diálogo se cierra con sell_close, no hace falta un
    segundo confirm."""
    inp.click(get_point("sell_top_slot"))
    time.sleep(SLEEP_AFTER_SELECT)
    inp.click(get_point("sell_top_confirm_1"))
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


def _dump_accept_candidates() -> None:
    """Diagnóstico: barrido de TODA la pantalla buscando accept_salvage.png
    con piso bajo (no solo pass/fail contra el threshold real), para ver
    dónde está de verdad en vez de adivinar la región. Guarda screenshot +
    crops en tools/debug_output/ (git-tracked, llega por push/pull)."""
    DEBUG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    tpl = cv2.imread(str(ACCEPT_SALVAGE), 0)
    if tpl is None:
        raise FileNotFoundError(ACCEPT_SALVAGE)
    th, tw = tpl.shape[:2]

    gray = vision.capture_screen(region=None, color=False)
    color = vision.capture_screen(region=None, color=True)
    cv2.imwrite(str(DEBUG_OUT_DIR / "accept_salvage_full.png"), color)

    result = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
    lines = [f"accept_salvage: piso {DEBUG_FLOOR}"]
    h, w = gray.shape[:2]
    for _ in range(DEBUG_MAX_MATCHES):
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < DEBUG_FLOOR:
            break
        x, y = max_loc[0] + tw // 2, max_loc[1] + th // 2
        lines.append(f"  score={max_val:.3f}  pos=({x},{y})")
        x0, y0 = max(0, x - DEBUG_CROP_HALF), max(0, y - DEBUG_CROP_HALF)
        x1, y1 = min(w, x + DEBUG_CROP_HALF), min(h, y + DEBUG_CROP_HALF)
        crop = color[y0:y1, x0:x1]
        cv2.imwrite(str(DEBUG_OUT_DIR / f"accept_salvage_crop_{max_val:.3f}_{x}_{y}.png"), crop)
        x0m = max(0, max_loc[0] - tw // 2)
        y0m = max(0, max_loc[1] - th // 2)
        x1m = min(result.shape[1], max_loc[0] + tw // 2 + 1)
        y1m = min(result.shape[0], max_loc[1] + th // 2 + 1)
        result[y0m:y1m, x0m:x1m] = 0

    (DEBUG_OUT_DIR / "accept_salvage_report.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"[exotics] guardado en {DEBUG_OUT_DIR}")


def test_debug_accept():
    """Arma el kit, clickea exotic_slot_1 (para que el diálogo salga en
    pantalla) y hace un barrido de TODA la pantalla buscando accept_salvage
    con piso bajo. Para diagnosticar con datos reales dónde aparece de
    verdad. `py -m bot exotics debug_accept`"""
    _arm_silver_fed()
    inp.click(get_point("exotic_slot_1"))
    time.sleep(SLEEP_AFTER_SALVAGE_CLICK)
    _dump_accept_candidates()


def _click_accept_salvage(timeout: float = 2.0) -> bool:
    btn = vision.wait_for(ACCEPT_SALVAGE, region=salvage.ACCEPT_REGION,
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
    print("[exotics] OK")
